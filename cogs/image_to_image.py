import discord
import requests
import os, io, base64
from discord.ext import commands
from discord.commands import slash_command, Option
from dotenv import load_dotenv
from .common.options import model_options, sampler_options, style_preset_options, clip_guidance_preset_options
from .common.messages import *
import json

load_dotenv()
API_HOST = os.getenv('API_HOST', 'https://api.stability.ai')
API_KEY = os.getenv("STABILITY_API_KEY")
if not API_KEY:
    raise EnvironmentError("Missing Stability API key.")

class IMG2IMG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="img2img", description=IMAGINE_DESCRIPTION)
    async def img2img(self, ctx,
                      #オプションにファイル添付を追加
                      attachments: Option(discord.Attachment, ATTACHMENT_OPTION_DESC, required=True),
                      prompt: Option(str, PROMPT_OPTION_DESC, required=True),
                      negative_prompt: Option(str, NEGATIVE_PROMPT_OPTION_DESC, required=False, default=""),
                      image_strength: Option(float, IMAGE_STRENGTH_OPTION_DESC, required=False, min_value=0.0, max_value=1.0),
                      cfg_scale: Option(float, CFG_SCALE_OPTION_DESC, required=False, min_value=0.0, max_value=35.0),
                      clip_guidance_preset: Option(str, CLIP_GUIDANCE_PRESET_OPTION_DESC, choices=list(clip_guidance_preset_options.keys()), required=False, default="NONE"),
                      style: Option(str, STYLE_OPTION_DESC, choices=list(style_preset_options.keys()), required=False, default="None"),
                      sampler: Option(str, SAMPLER_OPTION_DESC, choices=list(sampler_options.keys()), required=False),
                      seed: Option(int, SEED_OPTION_DESC, required=False, min_value=0, max_value=4294967295),
                      # model: Option(str, MODEL_OPTION_DESC, choices=list(model_options.keys()), required=False, default="Stable Diffusion XL 1.0")
                      ):
                   
        await ctx.defer()

        response = requests.get(attachments.url)
        image_data = response.content

        model = "Stable Diffusion 1.6"
        response = requests.post(f"{API_HOST}/v1/generation/{model_options[model]}/image-to-image", 
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {API_KEY}",
            },
            files={
                "init_image": image_data,
            },
            data={
                "text_prompts[0][text]": prompt,
                "text_prompts[0][weight]": 1,
                **({"text_prompts[1][text]": negative_prompt} if negative_prompt else {}),
                **({"text_prompts[1][weight]": -1 } if negative_prompt else {}),
                "init_image_mode": "IMAGE_STRENGTH",
                **({"image_strength": image_strength} if image_strength else {}),
                "samples": 3,
                "steps": 50,
                **({"cfg_scale": cfg_scale} if cfg_scale else {}),
                **({"clip_guidance_preset": clip_guidance_preset}),
                **({"sampler": sampler} if sampler else {}),
                **({"style_preset": style_preset_options[style]} if style != "None" else {}),
                **({"seed": seed} if seed else {}),
            }
        )

        if response.status_code != 200:
            response_dict = json.loads(response.text)
            embed=discord.Embed(
                color=discord.Color.red(), 
                description=f"{response.status_code} {response.reason}：{response_dict['name']}",
            )
            embed.set_footer(text=response_dict['message'])
            await ctx.respond(embed=embed)
            return
        
        file = discord.File(io.BytesIO(image_data), filename=f"image_orig.png")
        files = [file]
        seeds = f"  - image1: `original image`\n"
        nsfw_content_count = 0
        view = discord.ui.View()
        valid_image_index = -1 # 有効な画像のインデックスを追跡するための変数を追加
        for i, image in enumerate(response.json().get("artifacts", [])):
            
            if "SUCCESS" != image.get("finishReason") :
                nsfw_content_count += 1
                continue

            # ファイルを追加する前に、有効な画像のインデックスを更新
            files.append(discord.File(io.BytesIO(base64.b64decode(image["base64"])), filename=f"image{valid_image_index+1}.png"))
            seeds += f"  - image{valid_image_index+1}: `{image['seed']}`\n"
            
            button = discord.ui.Button(label=f"upscale {valid_image_index+1}", custom_id=f"{valid_image_index}")
            view.add_item(button)

            valid_image_index += 1  # ボタンを追加した後でインデックスをインクリメント

        embed = discord.Embed(
                description=
                    f"**{ctx.author.mention}'s Image to Image**\n\n" +
                    f"- model: `{model}`\n" +
                    f"- prompt: `{prompt}`\n" +
                    (f"- negative: `{negative_prompt}`\n" if negative_prompt else "") +
                    (f"- cfg_scale: `{cfg_scale}`\n" if cfg_scale else "") +
                    (f"- clip_guidance_preset: `{clip_guidance_preset}`\n" if clip_guidance_preset != "NONE" else "") +
                    (f"- sampler: `{sampler}`\n" if sampler else "") +
                    (f"- style_preset: `{style}`\n" if style != "None" else "") +
                    f"- seed:\n{seeds}" +
                    (f"\n\n") +
                    (ERROR_NSFW.format(nsfw_content_count) if nsfw_content_count !=0 else ""),
                color=discord.Color.blurple() 
                )
            

        embed.set_thumbnail(url=STABILITY_AI_LOGO_URL)
        embed.set_footer(text=f"created by {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        await ctx.respond(embed=embed, files=files, view=view)


        async def button_callback(interaction: discord.Interaction):
            await interaction.response.defer()

            original_message = interaction.message
            # button_callback内のcustom_idの取得方法を変更
            custom_id = int(interaction.data["custom_id"])

            # NSFW画像を考慮してインデックスを直接使用
            attachment_url = original_message.attachments[custom_id].url
            response = requests.get(attachment_url)

            if response.status_code != 200:
                embed=discord.Embed(
                    color=discord.Color.red(), 
                    description=ERROR_SYSTEM,
                )
                embed.set_footer(text=ERROR_RETRY)
                await interaction.followup.send(embed=embed)
                return  
            image_data = response.content

            engine_id = "esrgan-v1-x2plus"
            response = requests.post(
                f"{API_HOST}/v1/generation/{engine_id}/image-to-image/upscale",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {API_KEY}"
                },
                files={
                    "image": image_data
                }
            )

            files = []
            for i, image in enumerate(response.json().get("artifacts", [])):
                files.append(discord.File(io.BytesIO(base64.b64decode(image["base64"])), filename=f"image{i}.png"))

            embed = discord.Embed(
                description=
                    f"**{ctx.author.mention}'s UpScale**\n",
                color=discord.Color.blurple() 
            )

            embed.set_thumbnail(url=STABILITY_AI_LOGO_URL)
            embed.set_footer(text=f"created by {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
            await interaction.followup.send(embed=embed, files=files)

        for item in view.children:
            if isinstance(item, discord.ui.Button):
                item.callback = button_callback

def setup(bot):
    bot.add_cog(IMG2IMG(bot))