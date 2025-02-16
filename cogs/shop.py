import disnake
from disnake.ext import commands
from disnake import TextInputStyle
from yoomoney import Client, Quickpay
from utils.config import yoomoney_token, yoomoney_shet, adminlist, logid, roleid, guildid, iconurl, supporturl
import sqlite3
import random
import os
import asyncio

UPLOAD_DIR = "shop_files"

client = Client(yoomoney_token)

db = sqlite3.connect("dbs/shopdb.db")
cursor = db.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS shop (id INT, name TEXT, description TEXT, author TEXT, price INT, tovar TEXT, status INT)")
cursor.execute("CREATE TABLE IF NOT EXISTS users (id BIGINT, shopping INT, balance INT, buy_shop_id TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS payments (userid BIGINT, checkid VARCHAR, money INT)")
cursor.execute("CREATE TABLE IF NOT EXISTS promocode (pc TEXT, value INT, count INT, userid BIGINT)")
cursor.execute("CREATE TABLE IF NOT EXISTS buyres (tovar TEXT, user_id BIGINT)")

class ShopSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def start(self, inter):
        if inter.author.id not in adminlist:
            embed = disnake.Embed(title='Основное меню', description='Выберите категорию', color=disnake.Color.from_rgb(47,49,54))
            embed.set_thumbnail(url=inter.author.avatar) #Тут картинку поставить
            await inter.send(embed=embed, components=[
                disnake.ui.Button(label="Магазин", style=disnake.ButtonStyle.success, custom_id="shop", emoji='🛍️'),
                disnake.ui.Button(label="Профиль", style=disnake.ButtonStyle.blurple, custom_id="lk", emoji='👥'),
                [disnake.ui.Button(label="Поддержка", style=disnake.ButtonStyle.primary, emoji='💤', url=supporturl)]
            ])
        else:
            embed = disnake.Embed(title='Основное меню', description='Выберите категорию', color=disnake.Color.from_rgb(47,49,54))
            embed.set_thumbnail(url=inter.author.avatar) #Тут картинку поставить
            await inter.send(embed=embed, components=[
                disnake.ui.Button(label="Магазин", style=disnake.ButtonStyle.success, custom_id="shop", emoji='🛍️'),
                disnake.ui.Button(label="Профиль", style=disnake.ButtonStyle.blurple, custom_id="lk", emoji='👥'),
                [disnake.ui.Button(label="Поддержка", style=disnake.ButtonStyle.primary, emoji='💤', url=supporturl),
                disnake.ui.Button(label="Админ", style=disnake.ButtonStyle.gray, custom_id="adminpanel", emoji='🐖')]
            ])

    @commands.command()
    async def ashop(self, inter):
        if inter.author.id not in adminlist:
            embedfaq = disnake.Embed(title='Ошибка!', description='Идите нахуй, молодой человек!',
                                     color=disnake.Color.from_rgb(255, 0, 0))
            await inter.send(embed=embedfaq)
        else:
            prods = cursor.execute("SELECT id, name, price FROM shop WHERE status = 0").fetchall()
            embed = disnake.Embed(title='Управление Магазином', description='Товары/Категории: ',
                                  color=disnake.Color.from_rgb(47, 49, 54))
            for prod in prods:
                embed.add_field(name=prod[1], value=f'Цена: {prod[2]}₽ | ID: {prod[0]}', inline=False)
            await inter.send(embed=embed, components=[
                disnake.ui.Button(label="Добавить товар", style=disnake.ButtonStyle.success,
                                  custom_id="sadd"),
                disnake.ui.Button(label="Удалить товар", style=disnake.ButtonStyle.danger,
                                  custom_id="sremove"),
                [disnake.ui.Button(label="Удалить баланс", style=disnake.ButtonStyle.success,
                                  custom_id="delbal"),
                disnake.ui.Button(label="Добавить промокод", style=disnake.ButtonStyle.success,
                                  custom_id="baddpc")],
                disnake.ui.Button(label="Выдать баланс", style=disnake.ButtonStyle.secondary,
                                  custom_id="setbal")
            ])

    @commands.Cog.listener()
    async def on_dropdown(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id == 'buy_dropdown':
            tovar = cursor.execute("SELECT id, price, tovar FROM shop WHERE name =? AND status = 0",
                                   (inter.values[0],)).fetchone()
            user = cursor.execute("SELECT balance, shopping, buy_shop_id FROM users WHERE id =?",
                                  (inter.author.id,)).fetchone()

            user_purchases = cursor.execute("SELECT buy_shop_id FROM users WHERE id =?", (inter.author.id,)).fetchone()
            if user_purchases and str(tovar[0]) in user_purchases[0].split(", "):
                return await inter.response.send_message(
                    embed=disnake.Embed(title='Ошибка!',
                                        description='Вы уже приобрели этот товар. Пожалуйста, выберите что-то иное.\nЕсли, вы хотите воспользоваться купленным товаром,\n/start > Профиль > Скачать купленный товар.',
                                        color=disnake.Color.from_rgb(255, 0, 0)),
                    ephemeral=True
                )

            if not tovar:
                return await inter.response.send_message(
                    embed=disnake.Embed(title='Ошибка!',
                                        description='Товар уже продан,\nОбратитесь к продавцу за товаром',
                                        color=disnake.Color.from_rgb(255, 0, 0)),
                    ephemeral=True
                )
            if not user:
                cursor.execute("INSERT INTO users (id, shopping, balance, buy_shop_id) VALUES (?, 0, 0,'')",
                               (inter.author.id,))
                db.commit()
                return await inter.response.send_message(
                    embed=disnake.Embed(title='Ошибка!',
                                        description='Пользователь не найден, создайте новый профиль.\nДля этого зайдите в Личный кабинет.',
                                        color=disnake.Color.from_rgb(255, 0, 0)),
                    ephemeral=True
                )
            balance, shopping, buy_shop_id = user
            if balance < tovar[1]:
                return await inter.response.send_message(
                    embed=disnake.Embed(title='Ошибка!',
                                        description='Недостаточно средств на вашем личном кабинете,\nПожалуйста, пополните счет.',
                                        color=disnake.Color.from_rgb(255, 0, 0)),
                    ephemeral=True
                )
            embed = disnake.Embed(title='Вы точно хотите купить?',
                                  description=f'{inter.values[0]} за {tovar[1]}₽ \nУ вас есть 1 минута на решение!',
                                  color=disnake.Color.from_rgb(47, 49, 54))
            embed.set_footer(
                text='Прочитайте FAQ & Оферту, перед тем чем покупать! \nПроигнорируйте это сообщение если передумали')

            await inter.response.send_message(embed=embed, components=[
                disnake.ui.Button(label='Подтвердить', style=disnake.ButtonStyle.success, custom_id='accept', emoji='✅')
            ], ephemeral=True)
            try:
                """cursor.execute("UPDATE shop SET status = 1 WHERE id =?", (tovar[0],))
                                                                db.commit()"""
                interb = await self.bot.wait_for('button_click', timeout=60)
                balance -= tovar[1]
                shopping += 1
                if buy_shop_id:
                    buy_shop_id += f", {tovar[0]}"
                else:
                    buy_shop_id = str(tovar[0])
                cursor.execute("UPDATE users SET balance =?, shopping =?, buy_shop_id =? WHERE id =?",
                               (balance, shopping, buy_shop_id, inter.author.id))
                db.commit()

                tovar_content = tovar[2]

                if os.path.exists(os.path.join(UPLOAD_DIR, tovar_content)):
                    file_path = os.path.join(UPLOAD_DIR, tovar_content)
                    await interb.send(file=disnake.File(file_path), ephemeral=True)
                else:
                    # Assume 'tovar' is the actual content (text)
                    await interb.send(content=tovar_content, ephemeral=True)

                log_channel = await self.bot.fetch_channel(logid)
                await log_channel.send(embed=disnake.Embed(title="Новая покупка",
                                                           description=f"Покупатель: <@{inter.author.id}> \nТовар: {inter.values[0]}",
                                                           color=disnake.Color.from_rgb(47, 49, 54)))
                guild = await self.bot.fetch_guild(guildid)
                role = guild.get_role(roleid)
                await inter.author.add_roles(role)

            except Exception as e:
                cursor.execute("UPDATE shop SET status = 0 WHERE id =?", (tovar[0],))
                db.commit()
                print(f"Ошибка: {e}")

        if inter.component.custom_id == "download_select":
            selected_tovar_id = inter.values[0]
            tovar_info = cursor.execute(f"SELECT tovar FROM shop WHERE id = {selected_tovar_id}").fetchone()
            if tovar_info:
                tovar_content = tovar_info[0]
                if os.path.exists(os.path.join(UPLOAD_DIR, tovar_content)):
                    file_path = os.path.join(UPLOAD_DIR, tovar_content)
                    await inter.response.send_message(file=disnake.File(file_path), ephemeral=True)
                else:
                    # Если это не файл, отправляем как текстовое сообщение
                    await inter.response.send_message(content=tovar_content, ephemeral=True)
            else:
                await inter.response.send_message(
                    embed=disnake.Embed(title='Ошибка!', description='Не удалось найти выбранный товар.',
                                        color=disnake.Color.from_rgb(255, 0, 0)), ephemeral=True)
    @commands.Cog.listener("on_button_click")
    async def menu_listener(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id == "shop":
            try:
                prods = cursor.execute("SELECT id, name, description, author, price FROM shop WHERE status = 0").fetchall()
                embed = disnake.Embed(title='Магазин', description='Доступные товары', color=disnake.Color.from_rgb(47,49,54))
                names = []
                for prod in prods:
                    names.append(prod[1])
                dev = []
                options = []
                for prod in prods:
                    if names.count(f"{prod[1]}") > 1:
                        embed.add_field(name=prod[1], value=f'> Описание: `{prod[2]}`\n> Цена: `{prod[4]}`₽ | Кол-во: `Бесконечно`\n> Автор: `{prod[3]}`', inline=False)
                        options.append(disnake.SelectOption(
                            label=prod[1], description=f"Цена: {prod[4]}₽ | Кол-во: `Бесконечно`", emoji='🛒'))
                        for i in range(names.count(f"{prod[1]}")):
                            names.remove(prod[1])
                        dev.append(prod[1])
                    else:
                        if prod[1] in dev:
                            pass
                        else:
                            embed.add_field(name=prod[1], value=f'\n> Описание: `{prod[2]}`\n> Цена: `{prod[4]}`₽ | Кол-во: `Бесконечно`\n> \n> Автор: `{prod[3]}`', inline=False)
                            options.append(disnake.SelectOption(
                            label=prod[1], description=f"Цена: {prod[4]}₽ | Кол-во: 1", emoji='🛒'))
                await inter.response.send_message(embed=embed, ephemeral=True, components=[disnake.ui.Select(placeholder='Выберите товар', min_values=1, max_values=1, options=options, custom_id='buy_dropdown')])
            except:
              await inter.response.send_message(embed=embed, ephemeral=True)

        if inter.component.custom_id == 'baddpc':
            await inter.response.send_modal(title='Добавить промокод', custom_id='addpc', components=[
                disnake.ui.TextInput(
                    label="Промокод",
                    placeholder="PROMOCODE",
                    custom_id="pc",
                    style=TextInputStyle.short
                ),
                disnake.ui.TextInput(
                    label="Проценты",
                    placeholder="000",
                    custom_id="pcval",
                    style=TextInputStyle.short
                ),
                disnake.ui.TextInput(
                    label="Кол-во использований",
                    placeholder="10",
                    custom_id="pcount",
                    style=TextInputStyle.short
                )
            ])
        if inter.component.custom_id == "addbal":
            await inter.response.send_modal(title='Пополнить баланс', custom_id='gencheck', components=[
                disnake.ui.TextInput(
                    label="Сумма",
                    placeholder="Только целые числа!",
                    required=True,
                    custom_id="summa",
                    style=TextInputStyle.short
                ),
                disnake.ui.TextInput(
                    label="Промокод",
                    placeholder="Необязательно",
                    custom_id="promocode",
                    required=False,
                    style=TextInputStyle.short
                )
            ])
        if inter.component.custom_id == "sadd":
            await inter.response.send_modal(title='Добавить Товар', custom_id='addprod', components=[
                disnake.ui.TextInput(
                    label="Название",
                    placeholder="Название товара",
                    custom_id="name",
                    style=TextInputStyle.short,
                ),
                disnake.ui.TextInput(
                    label="Описание",
                    placeholder="Описание товара",
                    custom_id="description",
                    style=TextInputStyle.paragraph,
                ),
                disnake.ui.TextInput(
                    label="Автор",
                    placeholder="Автор товара",
                    custom_id="author",
                    style=TextInputStyle.short,
                ),
                disnake.ui.TextInput(
                    label="Цена",
                    placeholder="Цена товара",
                    custom_id="price",
                    style=TextInputStyle.short,
                )
            ])
        if inter.component.custom_id == "sremove":
            await inter.response.send_modal(title='Удалить товар', custom_id='removeprod', components=[
                disnake.ui.TextInput(
                    label="ID",
                    placeholder="ID Товара",
                    custom_id="id",
                    style=TextInputStyle.short,
                )
            ])

        if inter.component.custom_id == "setbal":
            await inter.response.send_modal(title="Выдать баланс", custom_id="msetbal", components=[
                disnake.ui.TextInput(
                    label="Айди участника",
                    placeholder="000000000000000",
                    custom_id="userid",
                    style=TextInputStyle.short,
                ),
                disnake.ui.TextInput(
                    label="Количество денег",
                    placeholder="00000",
                    custom_id="amount",
                    style=TextInputStyle.short,
                )
            ])

        if inter.component.custom_id == "delbal":
            await inter.response.send_modal(title="Выдать баланс", custom_id="mdelbal", components=[
                disnake.ui.TextInput(
                    label="Айди участника",
                    placeholder="000000000000000",
                    custom_id="userid",
                    style=TextInputStyle.short,
                )
            ])

        if inter.component.custom_id == 'oferta':
            embedoferta = disnake.Embed(title='Оферта', description='.',
                                        color=disnake.Color.from_rgb(47, 49, 54))
            await inter.response.send_message(embed=embedoferta, ephemeral=True)

        if inter.component.custom_id == 'more':
            embedfaq = disnake.Embed(title='Ошибка!', description='Функция временно недоступна!',
                                     color=disnake.Color.from_rgb(255, 0, 0))
            await inter.response.send_message(embed=embedfaq, ephemeral=True)

        if inter.component.custom_id == 'adminpanel':
            if inter.author.id not in adminlist:
                embedfaq = disnake.Embed(title='Ошибка!', description='Идите нахуй, молодой человек!',
                                         color=disnake.Color.from_rgb(255, 0, 0))
                await inter.response.send_message(embed=embedfaq, ephemeral=True)
            else:
                prods = cursor.execute("SELECT id, name, price FROM shop WHERE status = 0").fetchall()
                embed = disnake.Embed(title='Управление Магазином', description='Товары/Категории: ',
                                      color=disnake.Color.from_rgb(47, 49, 54))
                for prod in prods:
                    embed.add_field(name=prod[1], value=f'Цена: {prod[2]}₽ | ID: {prod[0]}', inline=False)
                await inter.send(embed=embed, ephemeral=True, components=[
                    disnake.ui.Button(label="Добавить товар", style=disnake.ButtonStyle.success,
                                      custom_id="sadd"),
                    disnake.ui.Button(label="Удалить товар", style=disnake.ButtonStyle.danger,
                                      custom_id="sremove"),
                    disnake.ui.Button(label="Удалить баланс", style=disnake.ButtonStyle.success,
                                      custom_id="delbal"),
                    disnake.ui.Button(label="Добавить промокод", style=disnake.ButtonStyle.success,
                                      custom_id="baddpc"),
                    disnake.ui.Button(label="Выдать баланс", style=disnake.ButtonStyle.secondary,
                                      custom_id="setbal")
                ])

        if inter.component.custom_id == 'lk':
            user = cursor.execute(
                f"SELECT shopping, balance, buy_shop_id FROM users WHERE id = {inter.author.id}").fetchone()
            if not user:
                cursor.execute(
                    f"INSERT INTO users (id, shopping, balance, buy_shop_id) VALUES ({inter.author.id}, 0, 0, '')")
                db.commit()
                user = cursor.execute(
                    f"SELECT shopping, balance, buy_shop_id FROM users WHERE id = {inter.author.id}").fetchone()

            embed = disnake.Embed(title=f'Профиль - {inter.author}',
                                  description=f'\n **Баланс: {user[1]}₽** \n**Куплено товаров: {user[0]}**\n\n> `💵` - Пополнить баланс\n> `🛒` - Скачать купленный ресурс\n\n**Купленные товары:**',
                                  color=disnake.Color.from_rgb(47, 49, 54))
            embed.set_thumbnail(url=inter.author.avatar.url)

            buy_shop_id = user[2]
            if buy_shop_id:
                buy_shop_id = buy_shop_id.split(', ')
                for id in buy_shop_id:
                    tovar = cursor.execute(f"SELECT name FROM shop WHERE id = {id}").fetchone()
                    if tovar:
                        embed.add_field(name=tovar[0], value=f'ID: {id}', inline=False)
                    else:
                        embed.add_field(name='Товар удален', value=f'ID: {id}', inline=False)
            else:
                embed.add_field(name='Нет купленных товаров',
                                value='Нажмите на кнопку "Скачать купленный ресурс" чтобы скачать товар', inline=False)

            await inter.response.send_message(embed=embed, ephemeral=True, components=[
                disnake.ui.Button(label="💵", style=disnake.ButtonStyle.success, custom_id="addbal"),
                disnake.ui.Button(label="🛒", style=disnake.ButtonStyle.success, custom_id="downloadtovar")
            ])

        if inter.component.custom_id == 'downloadtovar':
            user_id = inter.author.id
            buy_shop_id = cursor.execute(f"SELECT buy_shop_id FROM users WHERE id = {user_id}").fetchone()[0]
            if buy_shop_id:
                buy_shop_id = buy_shop_id.split(', ')
                options = []
                for id in buy_shop_id:
                    tovar = cursor.execute(f"SELECT name FROM shop WHERE id = {id}").fetchone()
                    if tovar:
                        options.append(
                            disnake.SelectOption(label=tovar[0], description="Нажмите чтобы скачать", value=id))
                if options:
                    embed = disnake.Embed(title='Выберите товар для скачивания:',
                                          description='Выберите товар из списка ниже.',
                                          color=disnake.Color.from_rgb(47, 49, 54))
                    await inter.response.send_message(embed=embed, ephemeral=True, components=[
                        disnake.ui.Select(placeholder="Выберите товар", min_values=1, max_values=1, options=options,
                                          custom_id="download_select")
                    ])
                else:
                    await inter.response.send_message(
                        embed=disnake.Embed(title='Ошибка!', description='У вас нет приобретённых товаров.',
                                            color=disnake.Color.from_rgb(255, 0, 0)), ephemeral=True)
            else:
                await inter.response.send_message(
                    embed=disnake.Embed(title='Ошибка!', description='У вас нет приобретённых товаров.',
                                        color=disnake.Color.from_rgb(255, 0, 0)), ephemeral=True)

    @commands.Cog.listener()
    async def on_modal_submit(self, inter: disnake.ModalInteraction):
        if inter.custom_id == "addpc":
            cursor.execute(
                f"INSERT INTO promocode (pc, value, count, userid) VALUES ('{inter.text_values['pc']}', {inter.text_values['pcval']}, {inter.text_values['pcount']}, {inter.author.id})")
            db.commit()
            await inter.response.send_message(f"Добавлен промокод: {inter.text_values['pc']}")

        if inter.custom_id == "addprod":
            await inter.response.defer(ephemeral=True)

            def check(m):
                return m.author == inter.author and (len(m.attachments) > 0 or m.content)

            try:
                await inter.followup.send("Пожалуйста, отправьте файл (или текст) в следующем сообщении.", ephemeral=True)
                msg = await self.bot.wait_for('message', check=check, timeout=60)

                file_name = None
                if msg.attachments:
                    attachment = msg.attachments[0]
                    random_name = f"{random.randint(0, 999999)}{os.path.splitext(attachment.filename)[1]}"
                    file_path = os.path.join(UPLOAD_DIR, random_name)
                    await attachment.save(file_path)
                    file_name = random_name
                else:
                    file_name = msg.content

                cursor.execute(
                    "INSERT INTO shop (id, name, description, author, price, tovar, status) VALUES (?, ?, ?, ?, ?, ?, 0)",
                    (random.randint(0, 999999), inter.text_values['name'], inter.text_values['description'],
                     inter.text_values['author'], inter.text_values['price'], file_name))
                db.commit()

                await inter.followup.send(f"Добавлен новый товар: {inter.text_values['name']}", ephemeral=True)

            except Exception as e:
                await inter.followup.send(f"Время ожидания истекло, попробуйте снова. Ошибка: {e}", ephemeral=True)

        if inter.custom_id == "removeprod":
            cursor.execute(f"DELETE FROM shop WHERE id = {inter.text_values['id']}")
            db.commit()
            await inter.response.send_message("Удалено", ephemeral=True)

        if inter.custom_id == "msetbal":
            try:
                bal = cursor.execute(
                    f"SELECT balance FROM users WHERE id = {int(inter.text_values['userid'])}").fetchone()
                fullbal = int(bal[0]) + int(inter.text_values['amount'])
                cursor.execute(f"UPDATE users SET balance = {fullbal} WHERE id = {inter.text_values['userid']}")
                await inter.response.send_message(
                    f"Выдал пользователю <@{inter.text_values['userid']}> {inter.text_values['amount']}₽")
                log_channel = await self.bot.fetch_channel(logid)
                embed = disnake.Embed(title="Выдан баланс",
                                      description=f"Пользователь: <@{inter.text_values['userid']}> \nСумма: {inter.text_values['amount']}₽ \n Админ: {inter.author.mention}",
                                      color=disnake.Color.from_rgb(47, 49, 54))
                await log_channel.send(embed=embed)
            except:
                await inter.response.send_message(
                    f"Похоже, пользователя нет в базе данных, и он ещё не использовал бота.")

        if inter.custom_id == "mdelbal":
            try:
                cursor.execute(f"UPDATE users SET balance = 0 WHERE id = {inter.text_values['userid']}")
                await inter.response.send_message(
                    f"Удалил баланс пользователю <@{inter.text_values['userid']}>")
                log_channel = await self.bot.fetch_channel(logid)
                embed = disnake.Embed(title="Очистка баланса",
                                      description=f"Пользователь: <@{inter.text_values['userid']}>\n Админ: {inter.author.mention}",
                                      color=disnake.Color.from_rgb(47, 49, 54))
                await log_channel.send(embed=embed)
            except:
                await inter.response.send_message(
                    f"Похоже, пользователя нет в базе данных, и он ещё не использовал бота.")

        if inter.custom_id == "gencheck":
            try:
                summa = int(inter.text_values['summa'])
                summaop = summa

                if summaop < 5 or summaop > 15000:
                    await inter.response.send_message("Сумма должна быть от 5 до 15000 рублей!", ephemeral=True)
                    return

                if inter.text_values['promocode']:
                    pc = cursor.execute(
                        f"SELECT value, count FROM promocode WHERE pc = '{inter.text_values['promocode']}'").fetchone()
                    if pc and pc[1] >= 1:
                        bonus = summa * pc[0] / 100
                        summa = int(round(summa + bonus))
                        pcount = pc[1] - 1
                        if pcount <= 0:
                            cursor.execute(f"DELETE FROM promocode WHERE pc = '{inter.text_values['promocode']}'")
                            db.commit()
                        else:
                            cursor.execute(
                                f"UPDATE promocode SET count = {pcount} WHERE pc = '{inter.text_values['promocode']}'")
                            db.commit()

                payment = Quickpay(
                    receiver=yoomoney_shet,
                    quickpay_form="shop",
                    targets=f"Пополнение баланса для {inter.author.id}",
                    paymentType="SB",
                    sum=summaop,
                    label=str(random.randint(1, 999999))
                )
                url = payment.redirected_url
                cursor.execute(
                    f"INSERT INTO payments (userid, checkid, money) VALUES ({inter.author.id}, '{payment.label}', {summa})")
                db.commit()

                embed = disnake.Embed(title='Оплата счёта',
                                      description=f'**Оплатите:** {summaop}₽ \n **Получите:** {summa}₽',
                                      color=disnake.Color.from_rgb(47, 49, 54))
                embed.set_footer(
                    text="Если вы оплатили, но не пришли деньги на баланс, подождите время.\nЕсли вы оплатили, но деньги не пришли спустя час или больше,\nНапишите в поддержку.")
                await inter.response.send_message(embed=embed, ephemeral=True, components=[
                    disnake.ui.Button(label='Оплатить', style=disnake.ButtonStyle.success, url=url)
                ])
            except ValueError:
                await inter.response.send_message("Введите только целые числа в поле суммы!")

async def checkoplata(bot, client):
    while True:
        await asyncio.sleep(10)
        oplats = cursor.execute("SELECT userid, checkid, money FROM payments").fetchall()
        for oplata in oplats:
            try:
                history = client.operation_history(label=oplata[1])
                if history.operations:
                    if history.operations[0].status == "success":
                        user = cursor.execute(f"SELECT balance FROM users WHERE id = {oplata[0]}").fetchone()
                        newbal = int(user[0]) + int(oplata[2])
                        cursor.execute(f"UPDATE users SET balance = {newbal} WHERE id = {oplata[0]}")
                        cursor.execute(f"DELETE FROM payments WHERE checkid = '{oplata[1]}'")
                        db.commit()
                        print(f"Платёж: {oplata[1]} был выполнен. Удаляю с базы данных...")
                        log_channel = await bot.fetch_channel(logid)
                        member = await bot.fetch_user(int(oplata[0]))
                        await member.send(f"Ваш баланс пополнен на {oplata[2]}₽!")
                        embed = disnake.Embed(
                            title="Пополнен баланс",
                            description=f"Пользователь: <@{oplata[0]}> \nСумма: {oplata[2]}",
                            color=disnake.Color.from_rgb(47, 49, 54)
                        )
                        await log_channel.send(embed=embed)

                    elif history.operations[0].status == "refused":
                        cursor.execute(f"DELETE FROM payments WHERE checkid = '{oplata[1]}'")
                        db.commit()
                        embedopp = disnake.Embed(
                            title="Ошибка",
                            description=f"У вас недостаточно средств \nОплата не засчитана.",
                            color=disnake.Color.from_rgb(47, 49, 54)
                        )
                        embedopp.set_footer(
                            text='Попробуйте в следующий раз, когда вам хватит денег на пополнение счета, либо уменьшите сумму пополнения.')
                        await member.send(embed=embedopp)
            except Exception as e:
                member = await bot.fetch_user(int(oplata[0]))
                await member.send(
                    f"Возникла ошибка при пополнении счета, Потеряно сооеденение с YooMoneyAPI, обратитесь в поддержку!")
                print(f"Ошибка при обработке платежа {oplata[1]}: {e}")
                return

def setup(bot: commands.Bot):
    bot.add_cog(ShopSystem(bot))
    bot.loop.create_task(checkoplata(bot, client))
