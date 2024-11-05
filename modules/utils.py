import random
import time

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 10; SM-G975U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36",
]

def get_random_user_agent():
    user_agent = random.choice(user_agents)
    print(f"Using User-Agent: {user_agent}")
    return user_agent

def random_delay(min_delay=2, max_delay=7):
    """
    a random delay between min_delay and max_delay seconds.
    """
    delay = random.uniform(min_delay, max_delay)
    print(f"Waiting for {delay:.2f} seconds...")
    time.sleep(delay)
