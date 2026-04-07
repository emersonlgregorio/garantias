"""
Integração futura com gateways (Stripe / Iugu).

Mantenha chamadas de billing concentradas aqui para não espalhar detalhes de pagamento nas views.
"""


def create_checkout_session_stub(*, company_id: int, plan_id: int) -> dict:
    """Placeholder: redirecionamento para checkout do provedor."""
    raise NotImplementedError("Stripe/Iugu: configurar chaves e implementar fluxo de checkout.")


def webhook_handler_stub(payload: bytes, headers: dict) -> None:
    """Placeholder: validar assinatura do webhook e atualizar Subscription."""
    raise NotImplementedError("Stripe/Iugu: implementar webhook com verificação de assinatura.")
