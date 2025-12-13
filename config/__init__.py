import os
from datetime import timezone, timedelta
import dotenv

dotenv.load_dotenv()

ENV = os.environ.get("ENV", "local")
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMEZONE = timezone(timedelta(hours=8))

if ENV == "local":
    from config.local import *
elif ENV == "test":
    # from config.test import *
    raise NotImplementedError
elif ENV == "prod":
    # from config.prod import *
    raise NotImplementedError
else:
    raise ValueError("Invalid environment name")
