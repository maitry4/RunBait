"""
Supabase client singleton.
Import `supabase` from here anywhere you need DB access.
"""
from supabase import create_client, Client
from core.config import get_settings

_settings = get_settings()

supabase: Client = create_client(_settings.SUPABASE_URL, _settings.SUPABASE_KEY)
