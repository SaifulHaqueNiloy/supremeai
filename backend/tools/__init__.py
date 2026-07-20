# বাংলা মন্তব্য: টেস্ট ও মকিং সহজ করার জন্য টুলস নেমস্পেসে বিভিন্ন সাবমডিউল এক্সপোজ এবং sys.modules এ রেজিস্টার করা হলো
import sys

# isolated tests বা venv-এ sys.modules['tools'] KeyError এড়াতে সেলফ-ম্যাপিং
if "tools" not in sys.modules:
    sys.modules["tools"] = sys.modules[__name__]

from tools.ai_agents import browser_agent
from tools.code import image_to_code, pr_reviewer
from tools.devops import auto_coverage_improver
from tools.learning import model_trainer, skill_recommender, style_learner
from tools.localization import bangla_voice
from tools.mcp import mcp_cloud_deploy, mcp_github_cicd, mcp_supabase, mcp_workspace
from tools.media import multilingual_tts

sys.modules["tools.mcp_cloud_deploy"] = mcp_cloud_deploy
sys.modules["tools.mcp_github_cicd"] = mcp_github_cicd
sys.modules["tools.mcp_supabase"] = mcp_supabase
sys.modules["tools.mcp_workspace"] = mcp_workspace
sys.modules["tools.bangla_voice"] = bangla_voice
sys.modules["tools.model_trainer"] = model_trainer
sys.modules["tools.pr_reviewer"] = pr_reviewer
sys.modules["tools.skill_recommender"] = skill_recommender
sys.modules["tools.browser_agent"] = browser_agent
sys.modules["tools.style_learner"] = style_learner
sys.modules["tools.auto_coverage_improver"] = auto_coverage_improver
sys.modules["tools.image_to_code"] = image_to_code
sys.modules["tools.multilingual_tts"] = multilingual_tts

__all__ = [
    "mcp_cloud_deploy",
    "mcp_github_cicd",
    "mcp_supabase",
    "mcp_workspace",
    "bangla_voice",
    "model_trainer",
    "pr_reviewer",
    "skill_recommender",
    "browser_agent",
    "style_learner",
    "auto_coverage_improver",
    "image_to_code",
    "multilingual_tts",
]
