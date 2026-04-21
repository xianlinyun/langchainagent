import json
import os
from typing import Sequence

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict


def get_history(session_id: str) -> "FileChatMessageHistory":

	return FileChatMessageHistory(session_id, "./chat_history")


class FileChatMessageHistory(BaseChatMessageHistory):

	def __init__(self, session_id: str, storage_path: str) -> None:

		self.session_id = session_id
		self.storage_path = storage_path
		# 每个会话一个独立文件
		self.file_path = os.path.join(self.storage_path, self.session_id)

		# 确保存储目录存在
		os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

	def add_messages(self, messages: Sequence[BaseMessage]) -> None:

		# 先取出已有消息
		all_messages = list(self.messages)
		# 追加新消息
		all_messages.extend(messages)

		# BaseMessage -> dict，方便 JSON 序列化
		new_messages = [message_to_dict(message) for message in all_messages]

		with open(self.file_path, "w", encoding="utf-8") as f:
			json.dump(new_messages, f, ensure_ascii=False)

	@property
	def messages(self) -> list[BaseMessage]:

		try:
			with open(self.file_path, "r", encoding="utf-8") as f:
				messages_data = json.load(f)
				return messages_from_dict(messages_data)
		except FileNotFoundError:
			return []

	def clear(self) -> None:

		with open(self.file_path, "w", encoding="utf-8") as f:
			json.dump([], f, ensure_ascii=False)

