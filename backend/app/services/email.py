import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

RESEND_ENDPOINT = "https://api.resend.com/emails"


async def send_application_confirmation(
    to_email: str, full_name: str, job_title: str, company: str
) -> bool:
    """Send a confirmation email via Resend. Returns True on success.

    If RESEND_API_KEY is not set, we log and return False so local dev still works.
    """
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY is not set, skipping email to %s", to_email)
        return False

    html = f"""
    <div style="font-family: -apple-system, system-ui, sans-serif; max-width: 560px; margin: auto;">
      <h2 style="color: #111;">Hi {full_name},</h2>
      <p>Thanks for applying to <strong>{job_title}</strong> at <strong>{company}</strong>.</p>
      <p>We've received your application and the team will get back to you soon.</p>
      <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;" />
      <p style="color: #888; font-size: 12px;">This is an automated confirmation from Job Board.</p>
    </div>
    """

    payload = {
        "from": settings.RESEND_FROM,
        "to": [to_email],
        "subject": f"Application received — {job_title} @ {company}",
        "html": html,
    }
    headers = {"Authorization": f"Bearer {settings.RESEND_API_KEY}"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(RESEND_ENDPOINT, json=payload, headers=headers)
            if r.status_code >= 400:
                logger.error("Resend error %s: %s", r.status_code, r.text)
                return False
            return True
    except httpx.HTTPError:
        logger.exception("Failed to send email via Resend")
        return False
