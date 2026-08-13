import os
import threading
import time
import discord
from discord import app_commands
from flask import Flask
import requests

# --- [1] Web Service용 Flask 서버 및 셀프핑 설정 ---
app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is alive!", 200


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


def keep_alive():
    """10분마다 Render 웹서비스 URL로 셀프핑 전송"""
    service_url = os.environ.get("RENDER_EXTERNAL_URL")

    if not service_url:
        print("[Self-Ping] URL 설정 없음")
        return

    print(f"[Self-Ping] 시작됨 - 대상 URL: {service_url}")
    while True:
        time.sleep(600)
        try:
            res = requests.get(service_url)
            print(f"[Self-Ping] Ping 성공! 상태 코드: {res.status_code}")
        except Exception as e:
            print(f"[Self-Ping] Ping 실패: {e}")


# --- [2] 디스코드 봇 및 슬래시 명령어 클라이언트 설정 ---
TOKEN = os.environ.get("DISCORD_TOKEN")
MY_USER_ID = 1533983071794233354  # 지정하신 본인 사용자 ID


class PersonalBot(discord.Client):

    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # 전역 슬래시 명령어 동기화
        await self.tree.sync()


client = PersonalBot()


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


# --- 계좌 출력 공통 함수 ---
async def send_account_info(interaction: discord.Interaction):
    if interaction.user.id != MY_USER_ID:
        return await interaction.response.send_message(
            "권한이 없습니다.", ephemeral=True
        )

    embed = discord.Embed(
        title="🏦 입금 계좌 안내", color=discord.Color.green()
    )
    embed.add_field(name="은행", value="케이뱅크", inline=True)
    embed.add_field(name="예금주", value="ㄱㅎㅅ", inline=True)
    embed.add_field(name="계좌번호", value="`100-129-436062`", inline=False)
    embed.set_footer(text="복사하여 사용하세요.")

    await interaction.response.send_message(embed=embed)


# --- 수수료 계산 공통 함수 ---
async def calculate_fee(
    interaction: discord.Interaction, 금액: float, 수수료: float = 3.5
):
    if interaction.user.id != MY_USER_ID:
        return await interaction.response.send_message(
            "권한이 없습니다.", ephemeral=True
        )

    if 금액 <= 0 or 수수료 < 0:
        return await interaction.response.send_message(
            "⚠️ 올바른 금액과 수수료를 입력해 주세요.", ephemeral=True
        )

    fee_rate = 수수료 / 100.0
    fee_amount = 금액 * fee_rate
    received_amount = 금액 - fee_amount
    required_amount = 금액 / (1 - fee_rate)

    embed = discord.Embed(
        title="💳 코인 수수료 계산 결과", color=discord.Color.blue()
    )
    embed.add_field(name="🏷️ 적용 수수료", value=f"**{수수료}%**", inline=True)
    embed.add_field(name="💵 기준 금액", value=f"{금액:,.0f}원", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=False)

    embed.add_field(
        name="📥 실수령액 (입금 시)",
        value=f"• 수수료: `{fee_amount:,.0f}원`\n• 받는 금액: **`{received_amount:,.0f}원`**",
        inline=True,
    )
    embed.add_field(
        name="📤 필요 입금액 (목표 수령)",
        value=f"• 필요 금액: **`{required_amount:,.0f}원`**",
        inline=True,
    )

    embed.set_footer(text="개인 전용 수수료 계산기")

    await interaction.response.send_message(embed=embed)


# --- [3] 계좌 명령어 2개 등록 (/계좌, /ㄱㅈ) ---
@client.tree.command(name="계좌", description="케이뱅크 입금 계좌를 확인합니다.")
async def account_cmd(interaction: discord.Interaction):
    await send_account_info(interaction)


@client.tree.command(name="ㄱㅈ", description="케이뱅크 입금 계좌를 확인합니다.")
async def account_short_cmd(interaction: discord.Interaction):
    await send_account_info(interaction)


# --- [4] 계산 명령어 2개 등록 (/계산, /ㄱㅅ) ---
@client.tree.command(name="계산", description="수수료를 계산합니다.")
@app_commands.describe(
    금액="계산할 금액 (예: 10000)",
    수수료="수수료율 % (미입력 시 기본 3.5%)",
)
async def calc_cmd(
    interaction: discord.Interaction, 금액: float, 수수료: float = 3.5
):
    await calculate_fee(interaction, 금액, 수수료)


@client.tree.command(name="ㄱㅅ", description="수수료를 계산합니다.")
@app_commands.describe(
    금액="계산할 금액 (예: 10000)",
    수수료="수수료율 % (미입력 시 기본 3.5%)",
)
async def calc_short_cmd(
    interaction: discord.Interaction, 금액: float, 수수료: float = 3.5
):
    await calculate_fee(interaction, 금액, 수수료)


# --- [5] 실행부 ---
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    ping_thread = threading.Thread(target=keep_alive, daemon=True)
    ping_thread.start()

    if TOKEN:
        client.run(TOKEN)
    else:
        print("에러: DISCORD_TOKEN 환경 변수가 설정되지 않았습니다.")
