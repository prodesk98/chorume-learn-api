from requests import post, get
import unittest
from config import env


def request(url: str, m: str = "get", payload: dict = None, params: dict = None,
            headers: dict = None, wait_status: int = 200) -> bool:
    if headers is None:
        headers = {"Authorization": f"Bearer {env.LEARN_TOKEN}"}

    if m == "get":
        if params is None:
            params = {}
        return get(url=url, headers=headers, params=params).status_code == wait_status

    if m == "post":
        if payload is None:
            payload = {}

        return post(url=url, headers=headers, json=payload).status_code == wait_status

    return False


class APITest(unittest.TestCase):
    def test_upsert(self):
        self.assertEqual(
            first=request(
                url="http://localhost:3001/api/upsert",
                m="post",
                headers=None,
                params=None,
                payload={
                    "content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin placerat venenatis pharetra. "
                               "Pellentesque fringilla dignissim velit quis hendrerit. Sed in urna nisi. Nunc massa velit, "
                               "tristique id rutrum non, blandit eu erat. Duis tempor pretium leo in semper. \n\n"
                               "Phasellus vitae sem faucibus, rutrum lorem at, tempor velit. Donec vulputate euismod quam id bibendum. "
                               "Pellentesque egestas non nisl eget ultrices. Etiam ut ex sit amet ipsum rutrum laoreet condimentum sed tortor. \n\n"
                               "Nam in interdum libero, sed accumsan dolor. Curabitur rhoncus laoreet nunc vitae euismod. Phasellus quam tortor, "
                               "dapibus sit amet condimentum ac, laoreet posuere felis. Pellentesque dapibus, lorem sed pharetra sollicitudin, "
                               "sapien ligula interdum dui, sed pharetra magna tortor eget diam. Praesent nec posuere turpis. \n\n"
                               "Curabitur id faucibus velit, et rutrum lectus.",
                    "username": "username"
                },
                wait_status=200
            ),
            second=True
        )

    def test_semantic_search(self):
        self.assertEqual(
            first=request(
                url="http://localhost:3001/api/semantic-search",
                m="get",
                headers=None,
                payload=None,
                params={
                    "q": "Pellentesque"
                },
                wait_status=200
            ),
            second=True
        )

    def test_asking(self):
        self.assertEqual(
            first=request(
                url="http://localhost:3001/api/asking",
                m="post",
                headers=None,
                payload={
                  "q": "Pellentesque",
                  "username": "Proton"
                },
                params=None
            ),
            second=True
        )

    def test_text_to_speech(self):
        self.assertEqual(
            first=request(
                url="http://localhost:3001/api/text-to-speech",
                m="post",
                headers=None,
                payload={
                    "content": "Eu programo em Python"
                },
                params=None
            ),
            second=True
        )

    def test_play_voice(self):
        self.assertEqual(
            first=request(
                url="http://localhost:3001/api/voice-playback-queue",
                m="post",
                headers=None,
                payload={
                    "channel_id": None,
                    "audio": "https://file-examples.com/storage/fe1dc579bf65a4de0965a48/2017/11/file_example_MP3_700KB.mp3"
                },
                params=None
            ),
            second=True
        )

    def test_million_show(self):
        self.assertEqual(
            first=request(
                url="http://localhost:3001/api/million-show",
                m="post",
                headers=None,
                payload={
                    "theme": "",
                    "amount": 3
                },
                params=None
            ),
            second=True
        )

    def test_get_all_vectors(self):
        self.assertEqual(
            first=request(
                url="http://localhost:3001/api/vectors",
                m="post",
                headers=None,
                payload={
                  "filter": {
                    "created_by": "Proton"
                  },
                  "skip": 0,
                  "limit": 15,
                  "sort": {
                    "_id": -1
                  }
                },
                params=None,
            ),
            second=True
        )


if __name__ == "__main__":
    unittest.main()
