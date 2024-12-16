import os


async def create_file_profile(file_name: int | str) -> str:
    path = f"./media/profiles/{str(file_name)}"
    if str(file_name) not in os.listdir("./media/profiles/"):
        os.mkdir(path)
        return path