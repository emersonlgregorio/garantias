"""Geração de PDF do mapa com polígonos selecionados (somente geometrias)."""

from __future__ import annotations

import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseBadRequest
from django.template.loader import render_to_string
from django.views import View
from weasyprint import HTML

from apps.guarantees.models import Guarantee
from apps.properties.models import Area


def _area_queryset_for_user(request):
    user = request.user
    if not user.is_authenticated:
        return Area.objects.none()
    if user.is_superuser:
        return Area.objects.select_related("property")
    cid = getattr(user, "company_id", None)
    if cid is None:
        return Area.objects.none()
    return Area.objects.select_related("property").filter(property__company_id=cid)


def _walk_geojson_coords(gj: dict, xs: list, ys: list) -> None:
    t = gj.get("type")
    if t == "Polygon":
        for ring in gj.get("coordinates") or []:
            for pt in ring:
                if len(pt) >= 2:
                    xs.append(float(pt[0]))
                    ys.append(float(pt[1]))
    elif t == "MultiPolygon":
        for poly in gj.get("coordinates") or []:
            for ring in poly:
                for pt in ring:
                    if len(pt) >= 2:
                        xs.append(float(pt[0]))
                        ys.append(float(pt[1]))


def _ring_centroid(ring: list) -> tuple[float, float]:
    if not ring:
        return 0.0, 0.0
    n = len(ring)
    slon = sum(float(p[0]) for p in ring)
    slat = sum(float(p[1]) for p in ring)
    return slon / n, slat / n


def _polygon_paths_d(
    polygon_coords: list,
    minx: float,
    maxx: float,
    miny: float,
    maxy: float,
    vb_w: float,
    vb_h: float,
    pad: float,
) -> str:
    def proj(lon: float, lat: float) -> tuple[float, float]:
        dx = maxx - minx
        dy = maxy - miny
        if dx < 1e-9:
            x = vb_w / 2
        else:
            x = pad + (lon - minx) / dx * (vb_w - 2 * pad)
        if dy < 1e-9:
            y = vb_h / 2
        else:
            y = pad + (maxy - lat) / dy * (vb_h - 2 * pad)
        return x, y

    parts = []
    for ring in polygon_coords:
        pts = []
        for pt in ring:
            if len(pt) < 2:
                continue
            x, y = proj(float(pt[0]), float(pt[1]))
            pts.append(f"{x:.1f},{y:.1f}")
        if len(pts) >= 3:
            parts.append("M " + " L ".join(pts) + " Z")
    return " ".join(parts)


class MapAreasPdfView(LoginRequiredMixin, View):
    """POST JSON: { \"area_ids\": [1, 2, ...] } — mesma fazenda, áreas acessíveis ao usuário."""

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return HttpResponseBadRequest(
                "JSON inválido.", content_type="text/plain; charset=utf-8"
            )
        raw_ids = payload.get("area_ids")
        if not isinstance(raw_ids, list) or not raw_ids:
            return HttpResponseBadRequest(
                "Informe ao menos uma matrícula (area_ids).",
                content_type="text/plain; charset=utf-8",
            )
        try:
            id_set = {int(x) for x in raw_ids}
        except (TypeError, ValueError):
            return HttpResponseBadRequest(
                "IDs inválidos.", content_type="text/plain; charset=utf-8"
            )

        raw_gid = payload.get("guarantee_id")
        raw_csid = payload.get("crop_season_id")
        if raw_gid is None or raw_csid is None:
            return HttpResponseBadRequest(
                "Informe garantia e safra.",
                content_type="text/plain; charset=utf-8",
            )
        try:
            guarantee_pk = int(raw_gid)
            season_pk = int(raw_csid)
        except (TypeError, ValueError):
            return HttpResponseBadRequest(
                "IDs de garantia ou safra inválidos.",
                content_type="text/plain; charset=utf-8",
            )

        base_qs = _area_queryset_for_user(request)
        areas = list(base_qs.filter(pk__in=id_set).order_by("matricula"))
        found = {a.pk for a in areas}
        if found != id_set:
            return HttpResponse(
                "Alguma área não existe ou não pertence à sua empresa.",
                status=403,
                content_type="text/plain; charset=utf-8",
            )

        pids = {a.property_id for a in areas}
        if len(pids) != 1:
            return HttpResponseBadRequest(
                "Selecione matrículas de uma única fazenda.",
                content_type="text/plain; charset=utf-8",
            )

        prop = areas[0].property
        property_label = f"{prop.description} — {prop.city}"

        g_qs = Guarantee.objects.select_related("property", "crop_season")
        if not request.user.is_superuser:
            cid = getattr(request.user, "company_id", None)
            if cid is None:
                return HttpResponse(
                    "Sem empresa vinculada.",
                    status=403,
                    content_type="text/plain; charset=utf-8",
                )
            g_qs = g_qs.filter(company_id=cid)
        guarantee = g_qs.filter(pk=guarantee_pk).first()
        if not guarantee:
            return HttpResponse(
                "Garantia não encontrada.",
                status=403,
                content_type="text/plain; charset=utf-8",
            )
        if guarantee.property_id != prop.id:
            return HttpResponseBadRequest(
                "A garantia deve ser da mesma fazenda das matrículas selecionadas.",
                content_type="text/plain; charset=utf-8",
            )
        if guarantee.crop_season_id is None:
            return HttpResponseBadRequest(
                "Cadastre a safra desta garantia antes de imprimir.",
                content_type="text/plain; charset=utf-8",
            )
        if guarantee.crop_season_id != season_pk:
            return HttpResponseBadRequest(
                "A garantia não pertence à safra indicada.",
                content_type="text/plain; charset=utf-8",
            )

        season = guarantee.crop_season
        crop_season_label = season.name if season else "—"
        guarantee_label = (
            f"{guarantee.get_type_display()} — #{guarantee.pk} — {guarantee.status}"
        )

        map_image_data_uri = None
        raw_snap = payload.get("map_snapshot_base64")
        if raw_snap and isinstance(raw_snap, str) and raw_snap.strip():
            s = raw_snap.strip()
            if s.startswith("data:image"):
                map_image_data_uri = s
            else:
                map_image_data_uri = "data:image/png;base64," + s

        xs: list[float] = []
        ys: list[float] = []
        geoms: list[tuple[Area, dict]] = []
        for area in areas:
            gj = json.loads(area.geometry.geojson)
            geoms.append((area, gj))
            _walk_geojson_coords(gj, xs, ys)

        if not xs:
            return HttpResponseBadRequest(
                "Geometria vazia.", content_type="text/plain; charset=utf-8"
            )

        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        dx = maxx - minx
        dy = maxy - miny
        frac = 0.04
        minx -= dx * frac if dx > 1e-9 else 0.01
        maxx += dx * frac if dx > 1e-9 else 0.01
        miny -= dy * frac if dy > 1e-9 else 0.01
        maxy += dy * frac if dy > 1e-9 else 0.01

        vb_w, vb_h = 820.0, 520.0
        pad = 28.0

        dx2 = maxx - minx
        dy2 = maxy - miny

        def proj_ll(lon: float, lat: float) -> tuple[float, float]:
            if dx2 < 1e-9:
                xx = vb_w / 2
            else:
                xx = pad + (lon - minx) / dx2 * (vb_w - 2 * pad)
            if dy2 < 1e-9:
                yy = vb_h / 2
            else:
                yy = pad + (maxy - lat) / dy2 * (vb_h - 2 * pad)
            return xx, yy

        svg_polys: list[dict] = []
        labels: list[dict] = []

        for area, gj in geoms:
            col = area.color or "#3388ff"
            t = gj.get("type")
            if t == "Polygon":
                d = _polygon_paths_d(
                    gj["coordinates"], minx, maxx, miny, maxy, vb_w, vb_h, pad
                )
                if d:
                    svg_polys.append({"path": d, "stroke": col, "fill": col})
                ring0 = gj["coordinates"][0] if gj.get("coordinates") else []
                c_lon, c_lat = _ring_centroid(ring0)
            elif t == "MultiPolygon":
                first_ring = None
                for poly in gj.get("coordinates") or []:
                    d = _polygon_paths_d(poly, minx, maxx, miny, maxy, vb_w, vb_h, pad)
                    if d:
                        svg_polys.append({"path": d, "stroke": col, "fill": col})
                    if poly and first_ring is None:
                        first_ring = poly[0]
                c_lon, c_lat = _ring_centroid(first_ring or [])
            else:
                continue

            lx, ly = proj_ll(c_lon, c_lat)
            labels.append(
                {"x": f"{lx:.1f}", "y": f"{ly:.1f}", "text": area.matricula}
            )

        body = render_to_string(
            "map/areas_pdf.html",
            {
                "property_label": property_label,
                "crop_season_label": crop_season_label,
                "guarantee_label": guarantee_label,
                "matriculas_list": ", ".join(a.matricula for a in areas),
                "vb_w": int(vb_w),
                "vb_h": int(vb_h),
                "svg_polys": svg_polys,
                "labels": labels,
                "map_image_data_uri": map_image_data_uri,
                "has_map_snapshot": bool(map_image_data_uri),
            },
            request=request,
        )
        pdf_bytes = HTML(
            string=body, base_url=request.build_absolute_uri("/")
        ).write_pdf()
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="mapa-matriculas.pdf"'
        return response
