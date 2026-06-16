import re

file_path = r'c:\Users\ids\test bot\eduquiz_bot\app\handlers\teacher.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add lock in cb_new_test
content = content.replace(
    '        stmt = select(func.count(Test.id)).where(Test.teacher_id == user.id)',
    '        await session.scalar(select(User.id).where(User.id == user.id).with_for_update())\n        stmt = select(func.count(Test.id)).where(Test.teacher_id == user.id)'
)

# 2. Add limit check + lock in teacher_upload
original_upload = """            db_user = await get_user_by_tg_id(session, message.from_user.id)
            if not db_user:
                await message.answer("Siz ro'yxatdan o'tmagansiz!")
                return
            test = await create_test(session, db_user.id, title)"""

new_upload = """            db_user = await get_user_by_tg_id(session, message.from_user.id)
            if not db_user:
                await message.answer("Siz ro'yxatdan o'tmagansiz!")
                return

            await session.scalar(select(User.id).where(User.id == db_user.id).with_for_update())
            stmt_count = select(func.count(Test.id)).where(Test.teacher_id == db_user.id)
            total_tests = (await session.execute(stmt_count)).scalar() or 0
            if total_tests >= db_user.max_tests:
                await message.answer(f"⚠️ Test yaratish limiti tugadi. Limitingiz: {db_user.max_tests} ta test.")
                return

            test = await create_test(session, db_user.id, title)"""
content = content.replace(original_upload, new_upload)

# 3. Add commit inside teacher_upload loops
content = content.replace(
    '                await add_question(session, test.id, i, pq.text, opts)\n\n        # Upload question images',
    '                await add_question(session, test.id, i, pq.text, opts)\n            await session.commit()\n\n        # Upload question images'
)

# 4. Global append for standalone service calls
def append_commit(match):
    full_call = match.group(1)
    indent = match.group(2)
    return full_call + '\n' + indent + 'await session.commit()'

# This matches single-line or multi-line function calls until the closing parenthesis
content = re.sub(
    r'(^([ \t]+)await (?:update_test_settings|set_test_status|set_correct_answer|set_question_image)\([^)]*\))', 
    append_commit, 
    content, 
    flags=re.MULTILINE
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch applied to teacher.py")
