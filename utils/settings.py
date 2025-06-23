import aiohttp

_KEY_SETTINGS = {
    'match_token_cost': 'Match token cost',
    'minimal_match_dollar_cost': 'Minimal match dollar cost',
    'experience_for_match': 'Experience for match',
    'project_win_tax': 'Project win tax',
    'referral_win_tax': 'Referral win tax',
    'project_withdraw_fixed_tax': 'Project withdraw fixed tax',
    'project_withdraw_share_tax': 'Project withdraw share tax',
    'referral_withdraw_share_tax': 'Referral withdraw share tax',
    'score_token_ratio': 'Score/token ratio',
    'support_duty_user': 'Support duty user',
    'tokens_variants': 'Bet variants (tokens)',
    'dollars_variants': 'Bet variants (dollars)',
}


def transform_settings_to_text(key):
    return _KEY_SETTINGS.get(key, None)
