# Author: Alexander D.
# Version 1.0
# IMPORTANT: See Line 262

import praw
import re
import random
from prawcore.exceptions import Redirect, Forbidden, NotFound

FILE_NAME = "digest_registry.txt"
HELP_TEXT = "Hello! I send interesting posts to you from any subreddit of your"\
            " choice! Simply type 'send {subreddit}. For example, if you " \
            "message 'send memes', I will send a post from r/memes. Please" \
            " note that I can only send posts from subreddits that are public."\
            " I can also send you multiple posts at once from the same " \
            "subreddit (up to 3 at a time). For example, 'send 2 memes' will " \
            "return two posts from r/memes."
DIGEST_TEXT = "Not enough time to check out your favourite subreddits? You can"\
              " use this bot to set up to 5 subreddits to display posts from! "\
              " First, reply with 'add {subreddit}' to add a subreddit to your" \
              " digest. Next, you can reply 'digest show' to display posts "\
              "from the subreddits you have added. Reply 'digest reset' to " \
              "reset your digest. You can use the same subreddit five times " \
              "and I will give you 5 posts from that subreddit if you'd like!"


# ################################# Classes ################################## #


class Post:
    """
    A class representing a unique post on reddit.
    === Parameters ===
    - url (str): represents the direct url of the post on reddit.
    - subreddit (str): represents the subreddit the post was posted in.
    """
    def __init__(self, sub_r: str) -> None:
        self.url = ''
        self.subreddit = sub_r

    def get_url(self, reddit) -> str:
        """
        Searches for a random post in the top 25 hot posts of the specified
        subreddit.
        === Parameters ===
        - reddit (Reddit): An instance of the Reddit class.

        Returns a string containing an error or the help text.
        """
        try:
            if self.subreddit == 'help!':
                return HELP_TEXT
            subreddit = reddit.subreddit(self.subreddit)
            num_post = random.randint(0, 24)
            for i, post in enumerate(subreddit.hot(limit=25)):
                if i == num_post:
                    self.url = 'https://www.reddit.com' + post.permalink
                    break
            return ''
        except Redirect or NotFound:
            return 'Subreddit not found. Try again!'
        except Forbidden:
            return f"It looks like r/{self.subreddit} is private. I can only send " \
                   f"posts from public subreddits!"


class Digest:
    """
    A class representing a reddit user's digest. A user can add up to 5
    subreddits to a library to display random posts from.
    === Parameters ===
    - name (str): The username of the reddit user.
    - library (list): A list of the subreddits the user would like posts from.
    The maximum length of library is 5.

    Precondition: name is a valid user on Reddit.
    """
    def __init__(self, name: str) -> None:
        self.name = name
        self.library = []

    def add_digest(self, sub_r: str, lines: list, msg) -> None:
        """
        Adds the given subreddit to the user's library. Checks to see if the
        user's library is not full. If not, the library is updated and the data
        file is updated accordingly.
        === Parameters ===
        - sub_r (str): Represents the subreddit the user wants to add to their
        digest.
        - lines (list): List containing the contents of digest_registry.txt',
        containing the user's previous digest data.
        - msg (Reddit.Message): Instance of message data from the user, used to
        reply and take commands from users.

        Returns nothing
        """
        if len(self.library) == 5:
            msg.reply('Sorry, your digest list is full.')
            return
        if self.name + '\n' in lines:
            lines.insert(lines.index(self.name + '\n') + 1, sub_r + '\n')
        else:
            lines.extend([self.name + '\n', sub_r + '\n', '\n'])
        self.library.append(sub_r)
        with open(FILE_NAME, 'w') as f:
            f.writelines(lines)
        msg.reply(f"{sub_r} was added to your digest!")

    def reset_digest(self, lines: list) -> None:
        """
        Resets the users digest. Clears the library and any records in the data
        file.
        === Parameters ===
        - lines (list): List containing the contents of digest_registry.txt',
        containing the user's previous digest data.

        Returns nothing
        """
        if self.name + '\n' in lines:
            i = 0
            while lines[lines.index(self.name + '\n') + i] != '\n':
                i += 1
            del(lines[lines.index(self.name + '\n'):lines.index(self.name + '\n') + i])
            self.library = []
        with open(FILE_NAME, 'w') as f:
            f.writelines(lines)

    def get_digest(self, reddit, msg) -> list:
        """
        Gives the user the digest. Checks the user's library for subreddits,
        then gathers posts from each entry in the library.
        === Parameters ===
        - reddit (Reddit): An instance of the Reddit class.
        - msg (Reddit.Message): Instance of message data from the user, used to
        reply and take commands from users.

        Returns a list of Post instances
        """
        urls = []
        lib = list(set(self.library))
        for sub in lib:
            num = self.library.count(sub)
            if num > 1:
                urls.extend(get_posts(sub, reddit, num, msg))
            else:
                p = Post(sub)
                error = p.get_url(reddit)
                if error:
                    msg.reply(error)
                    return []
                urls.append(p)
        return urls

    def digest_menu(self, reddit, msg, lines: list) -> (list, bool):
        """
        Determines if the user entered a digest-specific command and calls
        the correct function accordingly.
        === Parameters ===
        - reddit (Reddit): An instance of the Reddit class.
        - lines (list): List containing the contents of digest_registry.txt',
        containing the user's previous digest data.
        - msg (Reddit.Message): Instance of message data from the user, used to
        reply and take commands from users.

        Returns an empty list and a flag outlining if the command was
        digest-specific.
        """
        if msg.body.lower() == 'digest show':
            if self.library:
                msg.reply("Here's your digest for the day!")
                return self.get_digest(reddit, msg), True
            msg.reply("Your digest list is empty!")
        elif msg.body.lower() == 'digest reset':
            self.reset_digest(lines)
            msg.reply('You digest has been reset!')
        elif msg.body.lower() == 'digest help!':
            msg.reply(DIGEST_TEXT)
        else:
            return [], False
        return [], True

    def get_library(self, lines: list) -> None:
        """
        Reads the data file to determine the user's previously added subreddits
        to the library. Updates the user's library (self.library) accordingly.
        === Parameters ===
        - lines (list): List containing the contents of digest_registry.txt',
        containing the user's previous digest data.

        Returns nothing
        """
        if self.name + '\n' in lines:
            i = 0
            while lines[lines.index(self.name + '\n') + i] != '\n':
                i += 1
                self.library.append((lines[lines.index(self.name + '\n') + i].strip('\n')))
            if self.library[-1] == '\n' or self.library[-1] == '':
                del(self.library[-1])


# ############################### Functions ################################## #


def read_message(message) -> (int, str):
    """
    Reads message data from the user, determining if the user wants to add a
    subreddit to their digest or if the user wants up to 3 hot posts sent from
    a specified subreddit.
    === Parameters ===
    - msg (Reddit.Message): Instance of message data from the user, used to
    reply and take commands from users.

    Returns an int representing the quantity of posts to send and a str
    representing the subreddit to take posts from
    """
    msg = re.search(r'[sS]end [123]? ?\S{3,} *', message.body)
    dig = re.search(r'[aA]dd \S{3,} *', message.body)
    if msg is None and dig is None:
        message.reply("Hmmm, I didn't quite catch that. If you need help, "
                      "reply with 'send help!' or 'digest help!'.")
        return 0, ''
    if dig is not None:
        dig = dig.group()
        dig = dig[4:]
        return -1, dig
    msg = msg.group()
    msg = msg[5:]
    if msg[0] in ['1', '2', '3'] and msg[1] == ' ':
        return int(msg[0]), msg[2:].strip()
    return 1, msg.strip()


def get_posts(sub_r: str, reddit, num: int, msg) -> list:
    """
    Creates the number of post instances according to num from the specified
    subreddit then get the links for each post, making sure there are no
    duplicates.
    === Parameters ===
    - reddit (Reddit): An instance of the Reddit class.
    - msg (Reddit.Message): Instance of message data from the user, used to
    reply and take commands from users.
    - num (int): Number of post instances to create
    - sub_r (str): Represents subreddit of posts

    Returns a list of Post instances or the empty list
    """
    posts = [Post(sub_r) for i in range(num)]
    links = []
    for post in posts:
        error = post.get_url(reddit)
        while post.url in links:
            error = post.get_url(reddit)
        links.append(post.url)
        if error:
            msg.reply(error)
            return []
    return posts


# ############################## Main Program ################################ #

# client_secret, client_id, password info have been ommitted for privacy reasons
# As such, the program is not runnable in its current state.
reddit = praw.Reddit(client_id='',
                     client_secret='',
                     user_agent='<console:InterestPosts:1.0>',
                     username='interestpost-bot', password='')

while True:

    for item in reddit.inbox.unread():

        unread_message = item
        posts = []
        with open(FILE_NAME, 'r') as f:
            lines = f.readlines()
        d = Digest(unread_message.author.name)
        d.get_library(lines)
        posts, digest_flag = d.digest_menu(reddit, unread_message, lines)

        if not digest_flag:
            quantity, s_reddit = read_message(unread_message)
            if quantity == -1 and len(s_reddit) > 0:
                d.add_digest(s_reddit, lines, unread_message)
            elif quantity > 0 and len(s_reddit) > 0:
                posts = get_posts(s_reddit, reddit, quantity, unread_message)
                if posts:
                    unread_message.reply(f"Here's {quantity} post(s) from r/{s_reddit}!")

        for post in posts:
            unread_message.reply(post.url)

        item.mark_read()
