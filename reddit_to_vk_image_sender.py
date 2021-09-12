import vk_api, os, praw, time, requests, datetime, pathlib
from vk_api import VkUpload


class vk_reddit_sender:    
    def __init__(
        self,
        reddit_client_id: str,
        reddit_client_secret: str,
        vk_api_key: str,
        vk_is_group_chat: bool,
        vk_receiver_id: int,
        ):
        # set default variables
        self.allowed_extentions = ["png", "webp", "jpeg", "jpg"]
        self.vk_is_group_chat = False
        self.vk_first_message = ""
        self.subreddit = "all"
        self.post_limit = 15
    
        self.script_path = pathlib.Path(__file__).parent.resolve()
    
        # process input    
        self.reddit_client_id = reddit_client_id
        self.reddit_client_secret = reddit_client_secret
        
        self.vk_api_key = vk_api_key
        self.vk_is_group_chat = vk_is_group_chat
        self.vk_receiver_id = vk_receiver_id
        
        pass

    def get_vk(self) -> vk_api.VkApi:
        vk = vk_api.VkApi(token=self.vk_api_key).get_api()
        return vk

    def get_reddit(self) -> praw.Reddit: 
        reddit = praw.Reddit(
        client_id = self.reddit_client_id,
        client_secret = self.reddit_client_secret,
        redirect_uri="http://localhost:8080",
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) Gecko/20100101 Firefox/42.0",
        )

        reddit.read_only = True
        
        return reddit


    def get_file_extention(self, filename: str) -> str:
        extention = filename.split(".")[-1:][0]
        return extention

    def save_from_url(self, url: str, filename: str):
        content_bytes = requests.get(url).content
        
        with open(filename, "wb") as f:
            f.truncate()
            f.write(content_bytes)
        
        pass

    def run(self):
        # initialise vk and reddit clients
        vk = self.get_vk()
        reddit = self.get_reddit()
        
        # get posts from a subreddit
        subreddit = reddit.subreddit(self.subreddit)
        posts = subreddit.hot(limit = self.post_limit)


        first_message = True
        for post in posts:
            # skip stickied and pinned posts        
            if post.pinned or post.stickied:
                continue
            
            # temporarily save image from a Reddit post
            extention = self.get_file_extention(post.url)

            # skip non-image extentions
            if extention not in self.allowed_extentions:
                continue
            
            filename = f"temp_image.{extention}"
            full_path_to_temp_file = os.path.join(self.script_path, filename)
            self.save_from_url(post.url, full_path_to_temp_file)

            # upload it to VK
            uploader = VkUpload(vk)
            uploaded_img = uploader.photo_messages(full_path_to_temp_file)[0]
            
            # remove temporary image
            os.remove(full_path_to_temp_file)
            
            # send images to the chat
            if self.vk_is_group_chat and first_message:
                vk.messages.send(
                    chat_id = self.vk_receiver_id,
                    message = self.vk_first_message,
                    attachment = "photo{}_{}".format(uploaded_img['owner_id'], uploaded_img['id']),
                    random_id = 0)
                first_message = False
            elif self.vk_is_group_chat and not first_message:
                vk.messages.send(
                    chat_id = self.vk_receiver_id,
                    attachment = "photo{}_{}".format(uploaded_img['owner_id'], uploaded_img['id']),
                    random_id = 0)
            
            if not self.vk_is_group_chat and first_message:
                    vk.messages.send(
                        user_id = self.vk_receiver_id,
                        message = self.vk_first_message,
                        attachment = "photo{}_{}".format(uploaded_img['owner_id'], uploaded_img['id']),
                        random_id = 0)
                    first_message = False
            elif not self.vk_is_group_chat and not first_message:
                    vk.messages.send(
                        user_id = self.vk_receiver_id,
                        attachment = "photo{}_{}".format(uploaded_img['owner_id'], uploaded_img['id']),
                        random_id = 0)
                           
            # give VK a bit of rest 
            time.sleep(3)
        pass


if __name__ == "__main__":
    vk_api_key = ""
    reddit_client_id = ""
    reddit_client_secret = ""
    group_chat = False
    receiver_id = 0
    
    sender = vk_reddit_sender(
        reddit_client_id=reddit_client_id,
        reddit_client_secret=reddit_client_secret,
        vk_api_key=vk_api_key,
        vk_is_group_chat=group_chat,
        vk_receiver_id=receiver_id,
    )
    sender.run()
