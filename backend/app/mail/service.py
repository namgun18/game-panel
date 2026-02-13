import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import get_settings

settings = get_settings()


async def send_email(to: str, subject: str, body: str):
    """HTML 메일 발송"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.app_name} <{settings.smtp_from}>"
    msg["To"] = to
    msg.attach(MIMEText(body, "html", "utf-8"))

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user,
        password=settings.smtp_pass,
        start_tls=True,
    )


def _wrap_html(content: str) -> str:
    return f"""
    <div style="font-family: 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto;
                background: #1a1a2e; color: #e0e0e0; padding: 24px; border-radius: 8px;">
        {content}
        <hr style="border-color: #333; margin-top: 24px;">
        <p style="color: #666; font-size: 12px;">
            {settings.app_name} | {settings.app_url}
        </p>
    </div>
    """


# ─── 이메일 인증 코드 ───

async def send_verification_code(to: str, username: str, code: str):
    html = _wrap_html(f"""
        <h2 style="color: #4fc3f7;">📧 이메일 인증</h2>
        <p>{username}님, 아래 인증 코드를 입력해주세요.</p>
        <div style="background: #0d1117; padding: 20px; border-radius: 8px; margin: 16px 0;
                    text-align: center; font-size: 32px; letter-spacing: 8px;
                    font-family: monospace; color: #58a6ff;">
            {code}
        </div>
        <p style="color: #8b949e;">이 코드는 24시간 동안 유효합니다.</p>
    """)
    await send_email(to, f"[{settings.app_name}] 이메일 인증 코드: {code}", html)


# ─── 비밀번호 재설정 링크 ───

async def send_password_reset(to: str, username: str, reset_token: str):
    reset_url = f"{settings.app_url}/login?reset_token={reset_token}"
    html = _wrap_html(f"""
        <h2 style="color: #ffa726;">🔑 비밀번호 재설정</h2>
        <p>{username}님, 비밀번호 재설정을 요청하셨습니다.</p>
        <div style="text-align: center; margin: 20px 0;">
            <a href="{reset_url}"
               style="background: #238636; color: #fff; padding: 12px 32px;
                      border-radius: 8px; text-decoration: none; font-weight: 600;
                      display: inline-block;">
                비밀번호 재설정하기
            </a>
        </div>
        <p style="color: #8b949e;">이 링크는 1시간 동안 유효합니다.</p>
        <p style="color: #8b949e;">본인이 요청하지 않았다면 이 이메일을 무시하세요.</p>
    """)
    await send_email(to, f"[{settings.app_name}] 비밀번호 재설정", html)


# ─── 2FA 복구 코드 ───

async def send_2fa_recovery_code(to: str, username: str, code: str):
    html = _wrap_html(f"""
        <h2 style="color: #f85149;">🔓 2FA 복구</h2>
        <p>{username}님, 2FA 복구 요청을 받았습니다.</p>
        <p>아래 코드를 입력하면 기존 2FA가 해제되고, 다시 설정해야 합니다.</p>
        <div style="background: #0d1117; padding: 20px; border-radius: 8px; margin: 16px 0;
                    text-align: center; font-size: 32px; letter-spacing: 8px;
                    font-family: monospace; color: #f85149;">
            {code}
        </div>
        <p style="color: #8b949e;">이 코드는 15분간 유효합니다.</p>
        <p style="color: #f85149;">⚠️ 본인이 요청하지 않았다면 즉시 비밀번호를 변경하세요.</p>
    """)
    await send_email(to, f"[{settings.app_name}] 2FA 복구 코드: {code}", html)


# ─── 게임 서버 신청 알림 ───

async def send_game_request_notification(
    requester_name: str, requester_email: str,
    game_name: str, player_count: int,
    preferred_time: str, notes: str,
):
    html = _wrap_html(f"""
        <h2 style="color: #4fc3f7;">🎮 새 게임 서버 신청</h2>
        <table style="width: 100%; border-collapse: collapse;">
            <tr><td style="padding: 8px; font-weight: bold; color: #90caf9;">신청자</td>
                <td style="padding: 8px;">{requester_name}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold; color: #90caf9;">이메일</td>
                <td style="padding: 8px;">{requester_email or '미입력'}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold; color: #90caf9;">게임</td>
                <td style="padding: 8px;">{game_name}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold; color: #90caf9;">인원</td>
                <td style="padding: 8px;">{player_count}명</td></tr>
            <tr><td style="padding: 8px; font-weight: bold; color: #90caf9;">희망 시간대</td>
                <td style="padding: 8px;">{preferred_time or '미입력'}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold; color: #90caf9;">비고</td>
                <td style="padding: 8px;">{notes or '없음'}</td></tr>
        </table>
    """)
    await send_email(settings.admin_email, f"[게임서버 신청] {game_name} - {requester_name}", html)


# ─── 컨테이너 다운 알림 ───

async def send_container_down_alert(
    to: str, username: str, container_name: str, game_name: str,
):
    html = _wrap_html(f"""
        <h2 style="color: #ef5350;">⚠️ 게임 서버 다운 알림</h2>
        <p>{username}님, 아래 게임 서버가 중지되었습니다.</p>
        <div style="background: #2d1b1b; padding: 16px; border-radius: 4px; margin: 12px 0;">
            <strong style="color: #ff8a80;">서버:</strong> {container_name}<br>
            <strong style="color: #ff8a80;">게임:</strong> {game_name}
        </div>
        <p>관리 패널에서 서버 상태를 확인하세요.</p>
        <p style="color: #ffab91;">
            ※ 7일 이상 종료 상태가 지속되면 컨테이너가 자동 삭제됩니다.
        </p>
    """)
    await send_email(to, f"[⚠️ 서버 다운] {container_name} ({game_name})", html)


# ─── 삭제 예고 알림 ───

async def send_container_delete_warning(
    to: str, username: str, container_name: str, remaining_days: int,
):
    html = _wrap_html(f"""
        <h2 style="color: #ffa726;">🗑️ 게임 서버 삭제 예고</h2>
        <p>{username}님, 아래 서버가 <strong>{remaining_days}일 후</strong> 자동 삭제됩니다.</p>
        <div style="background: #2d2717; padding: 16px; border-radius: 4px; margin: 12px 0;">
            <strong>서버:</strong> {container_name}
        </div>
        <p>서버를 유지하려면 관리 패널에서 <strong>다시 시작</strong>해주세요.</p>
        <p style="color: #fff176;">
            ⚡ 서버를 시작하면 삭제 타이머가 초기화됩니다.
        </p>
    """)
    await send_email(to, f"[🗑️ 삭제 예고] {container_name} - {remaining_days}일 후 삭제", html)


# ─── 삭제 완료 알림 ───

async def send_container_deleted_notice(
    to: str, username: str, container_name: str, stopped_days: int,
):
    html = _wrap_html(f"""
        <h2 style="color: #e53935;">❌ 게임 서버 자동 삭제됨</h2>
        <p>{username}님, 아래 서버가 {stopped_days}일 이상 종료 상태여서 자동 삭제되었습니다.</p>
        <div style="background: #2d1b1b; padding: 16px; border-radius: 4px; margin: 12px 0;">
            <strong>서버:</strong> {container_name}
        </div>
        <p style="color: #ef9a9a;">
            ※ 볼륨 데이터는 보존되어 있습니다. 필요 시 관리자에게 복구를 요청하세요.
        </p>
    """)
    await send_email(to, f"[❌ 삭제됨] {container_name} 자동 삭제 완료", html)
