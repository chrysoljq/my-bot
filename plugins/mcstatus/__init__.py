import socket
import traceback

from .minecraft import StatusPing
from nonebot.plugin import on_command
from nonebot.params import CommandArg
from nonebot.adapters import Message
from nonebot.log import logger
mcstatus = on_command("server",aliases={"motd","mcstatus"})

@mcstatus.handle()
async def motd(args: Message=CommandArg()):
    try:
        # addr = addr.replace('&#91;','[').replace('&#93;',']')
        server = StatusPing(args.extract_plain_text())
        stat = server.get_status()
        # print(stat)
        # 提取基本信息
        if stat.get("text"):
            await mcstatus.send("服务器正在重启，请稍后再试")
        version = stat.get("version") if isinstance(stat.get("version"),str) else stat.get("version").get("name")
        
        try: 
            protocol = stat.get("version").get("protocol","未知")
        except:
            protocol = "未知"
        players = stat.get("players")
        if not players:
            await mcstatus.send('服务器正在启动，请稍后再重试')
        online = players.get("online")
        max_ = players.get("max")
        sample = [i.get("name") for i in players.get(
            "sample")] if players.get("sample") else []
        logger.info(stat)
        ping = stat.get("ping")
        # 描述文本
        description = stat.get("description")

        if isinstance(description,str):
            desc = description
        elif description.get('extra'):
            try:
                text = [t.get('text') for t in description.get('extra')]
                desc = ''.join(text)
            except:
                desc=description
        elif description.get('translate'):
            desc = description.get('translate')
        else:
            desc = description.get("text")
        # 只提取模组列表
        mods = 0
        ress = 0
        modstr = ""
        try:
            if stat.get("modinfo"):
                mods = len(stat.get("modinfo").get("modList"))
                modstr = f"模组数量：{mods}"
            elif stat.get("forgeData"):
                mods = len(stat.get("forgeData").get("mods"))
                ress = len(stat.get("forgeData").get("channels"))
                modstr = '资源包/模组数：'+str(ress)+'/'+str(mods)
        except Exception as e:
            traceback.print_exc()
        # 变成字符串
        newline = "\n"
        msg = f"""【服务器信息】
服务端版本：{version}
协议版本：{protocol}
当前人数：{online}/{max_}
{'玩家列表：'+'、'.join(sample)+newline if sample else ''}描述文本：{desc}
游戏延迟：{ping}ms{newline+modstr}"""
        await mcstatus.send(msg.strip())
    except socket.gaierror:
        await mcstatus.send("没有此服务器,[CQ:face,id=178],可能是域名解析错误")
    except socket.timeout:
        await mcstatus.send("连接超时")
    except Exception as e:
        traceback.print_exc()
        await mcstatus.send(str(e))