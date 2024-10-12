import os
import asyncio
import base64

import filetype

from typing import Union, Optional, Tuple, List, Any

from requests.sessions import RequestsCookieJar

from hugchat_lib.hugchat import ChatBot
from hugchat_lib.login import Login
from hugchat_lib.message import Message
from hugchat_lib.types.message import MessageNode, Conversation


ACCOUNT_LIST = [
    ("bhzxw5o@femailtor.com","TW9jaGFtYWQgUmFpdmFsZHk=")
]

DEFAULT_MODEL = "meta-llama/Llama-3.2-11B-Vision-Instruct"

# with open("./conv_id.txt", "r") as f: 
#     CONV_ID = f.read().strip()

class HuggingChat: 
    def __init__(
        self,
        email: str = "bhzxw5o@femailtor.com",
        password: str = "TW9jaGFtYWQgUmFpdmFsZHk=",
        cookies_dir: str = "./cookies",
        conversation_id: str = "",
    ): 
        if not os.path.exists(cookies_dir): 
            self.login()
        
        self.email = email
        self.password = password
        self.cookies_dir = cookies_dir
        self.cookies_fp = f"{self.cookies_dir}/{self.email}.json"
        self.conversation_id = conversation_id
        self.client = self.build_client()
        self.remote_conversations: List[Conversation] = self.client.get_remote_conversations().copy()
        self.conversation = self.client.current_conversation


    async def chat_async(
        self,
        prompt: str,
        image: Union[str, bytes] = None,
        history: Union[List[Any], List[MessageNode], None] = None, 
        system_prompt: str = "You are a helpful assistant!",
        model: str = DEFAULT_MODEL,
        return_completion: bool = False,
        **kwargs    
    ): 
        return await asyncio.to_thread(self.chat, prompt, image, history, system_prompt, model, return_completion)
    
    def chat(
        self,
        prompt: str,
        image: Union[str, bytes] = None,
        history: Union[List[Any], List[MessageNode], None] = None, 
        system_prompt: str = "You are a helpful assistant!",
        model: str = DEFAULT_MODEL,
        return_completion: bool = False,
        **kwargs
    ) -> Union[str, Message]: 
        # conv_remote = self.get_conv(CONV_ID, replace=True)
        # if conv_remote: 
        #     self.conversation = conv_remote

        self.client = self.build_client(model=model, system_prompt=system_prompt)
        resp_text = None

        if image: 
            image = self.get_image_data(image)

        completion = self.client.chat(
            text=prompt,
            img=image, 
        )

        resp_text = completion.text
        if return_completion: 
            return completion

        return resp_text

    def get_image_data(self, data: Union[str, bytes]) -> Tuple[str, str, None]: 
        if isinstance(data, str): 
            img_path = data
            if not os.path.exists(img_path): 
                raise Exception("Image not exists")
            
            with open(img_path, "rb") as f: 
                data = f.read()

        kind = filetype.guess(data)
        if not kind: 
            raise ValueError("Cannot determine file type")

        filename = f"base64;{os.urandom(8).hex()}.{kind.extension}"
        encoded_data = base64.b64encode(data).decode('utf-8')

        return filename, encoded_data, None
    
    def get_conv(self, conv_id: str, replace: bool = False) -> Optional[Conversation]: 
        get_conv_func = self.client.get_conversation_info
        del_conv_func = self.delete_conv

        curr_conv = self.client.current_conversation
        target_conv = None
        if not conv_id: 
            return target_conv
        
        try: 
            rmt_convs = self.remote_conversations
            for conv in rmt_convs: 
                if conv.id == conv_id: 
                    target_conv = get_conv_func(conv_id)
                elif conv.id == curr_conv.id: 
                    del_conv_func(conv.id)
            
            if replace and target_conv: 
                self.conversation = target_conv
        except: 
            pass

        return target_conv
    
    def delete_conv(self, id: Union[str, List[str]] = None): 
        convs = self.remote_conversations
        delete_conv_func = self.client.delete_conversation
        delete_all_conv_func = self.client.delete_all_conversations

        if not id: 
            return delete_all_conv_func()

        if id: 
            ids = []
            ids += [id]

            for conv in convs: 
                if conv.id in ids: 
                    delete_conv_func(conv)       
        
    def build_client(
        self,
        cookies: Union[RequestsCookieJar, dict, None] = None,
        cookie_path: Optional[str] = None,
        model: Union[int, str] = DEFAULT_MODEL,
        system_prompt: str = "You are a helpful assistant!",
        conversation_id: str = ""
    ): 
        conversation_id = self.conversation_id if not conversation_id else conversation_id
        cookie_path = self.cookies_fp

        return ChatBot(
            cookies=cookies,
            cookie_path=cookie_path,
            default_llm=model,
            system_prompt=system_prompt,
            conversation_id=conversation_id
        )

    def login(self) -> RequestsCookieJar: 
        login_obj = Login(self.email, self.password)
        login_obj.login(cookie_dir_path=self.cookies_dir, save_cookies=True)

async def main(): 
    conv_id = "67034198d2f5b17831e1a32a"
    hc = HuggingChat(conversation_id=conv_id)

    res = await hc.chat_async("halo", return_completion=True)
    print(res)
    return
    # print(hc.client.current_conversation.id, hc.conversation.id)
    # return

    prompt = "gambar apa ini bre"
    image = "./1.jpg"
    return_completion = True

    res = await hc.chat_async(prompt, image=image, return_completion=return_completion)
    # res = hc.chat("halo sayang", return_completion=return_completion)
    
    # hc = HuggingChat()
    # res = await hc.chat_async("sekarang boleh kamu jawab berapa hasilnya?", return_completion=return_completion)
    print(res.conversation.history)
    # hc.delete_conv()

if __name__ == "__main__": 
    asyncio.run(main())