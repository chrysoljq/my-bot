from nonebot.plugin import on_regex, on_message, on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot, permission

MY_GROUP = 1

async def not_me(event: GroupMessageEvent):
    return event.self_id != event.sender.user_id

async def is_mygroup(event: GroupMessageEvent):
    return event.self_id != event.sender.user_id and event.group_id == MY_GROUP

async def is_admin(event: GroupMessageEvent):
    return event.sender.role

rlc_new = on_regex(r"(?i)(?=.*新)(?=.*(?:攻略|教程))", rule=not_me)
rlc_tutor = on_regex(r"(?i)(?!.*新)(?=.*RLC)(?=.*(?:攻略|教程))", rule=not_me)
rlc_mount = on_regex(r"(?i)(?=.*(?:什么|怎么|咋))(?=.*(?:坐骑|飞行))", rule=not_me)
test = on_message(rule=is_mygroup)
# ban_user = on_command('ban',)


@rlc_tutor.handle()
async def rlc_all(bot: Bot, event: GroupMessageEvent):
    await bot.send_group_msg(message='[CQ:forward,id=wxkO4/HZzfEPkIzRYJHuasb8ooFTYPdYCagN1zVgvvhd4PYbSKcrC2gvDfo+roxl]', group_id=event.group_id)


@rlc_mount.handle()
async def rlc_mount_handle(bot: Bot, event: GroupMessageEvent):
    await bot.send_group_msg(message=' ', group_id=event.group_id)


@rlc_new.handle()
async def rlc_new_handle(bot: Bot, event: GroupMessageEvent):
    await bot.call_api(
        'send_group_msg',
        message='[CQ:json,data={"app":"com.tencent.forum"&#44;"config":{"ctime":1740139318&#44;"extendAutoSize":1&#44;"forward":1&#44;"token":"f38507f99be6beb752e54e0a0bc909b6"&#44;"type":"normal"}&#44;"desc":"频道帖子"&#44;"meta":{"detail":{"channel_info":{"channel_id":635712896&#44;"channel_name":"🌟攻略"&#44;"guild_icon":"https://groupprohead.gtimg.cn/637335054006580438/0?imageView2/1/w/100/h/100/format/&amp;t=1731047379857"&#44;"guild_id":637335054006580438&#44;"guild_name":"🍀RLCraft交流频道"&#44;"str_guild_id":"637335054006580438"}&#44;"create_at":1740139309&#44;"duration":86400000000000&#44;"feed":{"comment_count":8&#44;"contents":{"contents":&#91;{"text_content":{"text":"1.原木→木板 &amp; 木板→木棍"}&#44;"type":1}&#44;{"text_content":{"text":"①把原木/木板放置在地上，主手持斧子右键，即可将原木劈成木板，木板劈成木棍。"}&#44;"type":1}&#44;{"text_content":{"text":"此外，木棍还可以通过撸树叶、灌木获得。"}&#44;"type":1}&#44;{"text_content":{"text":"②锯子与原木/木板直接合成"}&#44;"type":1}&#44;{"text_content":{"text":"(锯子所需采集等级是使用等级，不影响合成)。"}&#44;"type":1}&#44;{"text_content":{"text":"2.手都撸爆了，撸不掉树怎么办？"}&#44;"type":1}&#44;{"text_content":{"text":"因「无树可撸」模组，玩家不能直接用手撸树，需要工具。"}&#44;"type":1}&#44;{"text_content":{"text":"①没有遇到工作台情况下："}&#44;"type":1}&#44;{"text_content":{"text":"挖砂砾得燧石，对着石头(石质方块)右键，变成燧石碎片，与木棍合成燧石小刀，再用小刀割草得植物纤维，合成线，然后用木棍+线+燧石碎片合成燧石斧，即可砍树做工作台。"}&#44;"type":1}&#93;}&#44;"create_time":1710992641&#44;"emotion_reaction":{"emoji_reaction_list":&#91;{"emoji_id":"76"&#44;"emoji_type":1}&#44;{"emoji_id":"311"&#44;"emoji_type":1}&#44;{"emoji_id":"271"&#44;"emoji_type":1}&#93;}&#44;"prefer_count":9&#44;"sub_title":{}&#44;"title":{"contents":&#91;{"text_content":{"text":"RLCraft 新手攻略杂谈"}&#44;"type":1}&#93;}&#44;"view_count":2572}&#44;"feed_id":"B_01adfb65e73604001441152186794455220X60"&#44;"invite_code":"2nj4TOx23Kh"&#44;"jump_url":"https://qun.qq.com/qqweb/qunpro/share?_wv=3&amp;_wwv=128&amp;appChannel=share&amp;inviteCode=2nj4TOx23Kh&amp;contentID=dHQWgC&amp;businessType=2&amp;jumpInfo=ClCndYMTfhcThYWSyUX%2Fj1G5v%2B1eEWf1NP%2BnL%2FBsqtCtzMcTuC%2BLYQs%2FN9EV6IdQcd2llgv8YVVn9CK0XtbDz93LcN6YGLSqJOoo6Ne2%2BELQ8BIDdnAx&amp;needOpenWeb=1&amp;funclist=5&amp;shareSource=1"&#44;"poster":{"avatar":"https://qqchannel-profile-1251316161.file.myqcloud.com/1688657132b2748c9767e72a1e/100?t=1688657133"&#44;"nick":"财迷ZERO"&#44;"str_tiny_id":"144115218679445522"&#44;"tiny_id":144115218679445522}&#44;"source":1&#44;"tag_type":1&#44;"token":"1740139309"}}&#44;"prompt":"&#91;频道帖子&#93;RLCraft 新手攻略杂谈"&#44;"ver":"1.0.0.1"&#44;"view":"rank"}]',
        group_id=event.group_id,
    )


@test.handle()
async def test_handle(bot: Bot, event: GroupMessageEvent):
    await bot.send_group_msg(message=event.raw_message, group_id=event.group_id, auto_escape=True)


