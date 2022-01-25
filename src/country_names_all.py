
COUNTRIES = {'American Samoa': 'AS', 'Argentina': 'AR', 'Aruba': 'AW', 'Australia': 'AU', 'Austria': 'AT', 'Bahrain': 'BH', 'Belarus': 'BY', 'Belgium': 'BE', 'Bermuda': 'BM', 'Brazil': 'BR', 'Bulgaria': 'BG', 'Canada': 'CA', 'Cayman Islands': 'KY', 'Chile': 'CL', 'Colombia': 'CO', 'Costa Rica': 'CR', 'Croatia': 'HR', 'Cyprus': 'CY', 'Denmark': 'DK', 'Dominican Republic': 'DO', 'Ecuador': 'EC', 'Egypt': 'EG', 'El Salvador': 'SV', 'Estonia': 'EE', 'Finland': 'FI', 'France': 'FR', 'French Polynesia': 'PF', 'Germany': 'DE', 'Greece': 'GR', 'Guadeloupe': 'GP', 'Guam': 'GU', 'Guatemala': 'GT', 'Honduras': 'HN', 'Hong Kong': 'HK', 'Hungary': 'HU', 'Iceland': 'IS', 'India': 'IN', 'Indonesia': 'ID', 'Ireland': 'IE', 'Israel': 'IL', 'Italy': 'IT', 'Japan': 'JP', 'Jordan': 'JO', 'Kuwait': 'KW', 'Latvia': 'LV', 'Lebanon': 'LB', 'Liechtenstein': 'LI', 'Lithuania': 'LT', 'Luxembourg': 'LU', 'Malaysia': 'MY', 'Malta': 'MT', 'Mexico': 'MX', 'Netherlands': 'NL', 'New Zealand': 'NZ', 'Nicaragua': 'NI', 'Nigeria': 'NG', 'Northern Mariana Islands': 'MP', 'Norway': 'NO', 'Oman': 'OM', 'Panama': 'PA', 'Papua New Guinea': 'PG', 'Paraguay': 'PY', 'Peru': 'PE', 'Philippines': 'PH', 'Poland': 'PL', 'Portugal': 'PT', 'Puerto Rico': 'PR', 'Qatar': 'QA', 'Romania': 'RO', 'Saudi Arabia': 'SA', 'Serbia': 'RS', 'Singapore': 'SG', 'Slovakia': 'SK', 'Slovenia': 'SI', 'South Africa': 'ZA', 'Spain': 'ES', 'Sweden': 'SE', 'Switzerland': 'CH', 'Thailand': 'TH', 'Turkey': 'TR', 'Turks and Caicos Islands': 'TC', 'Ukraine': 'UA', 'United Arab Emirates': 'AE', 'United Kingdom': 'GB', 'United States': 'US', 'Uruguay': 'UY'}

COUNTRIES_REVERSE = {'AS': 'American Samoa', 'AR': 'Argentina', 'AW': 'Aruba', 'AU': 'Australia', 'AT': 'Austria', 'BH': 'Bahrain', 'BY': 'Belarus', 'BE': 'Belgium', 'BM': 'Bermuda', 'BR': 'Brazil', 'BG': 'Bulgaria', 'CA': 'Canada', 'KY': 'Cayman Islands', 'CL': 'Chile', 'CO': 'Colombia', 'CR': 'Costa Rica', 'HR': 'Croatia', 'CY': 'Cyprus', 'DK': 'Denmark', 'DO': 'Dominican Republic', 'EC': 'Ecuador', 'EG': 'Egypt', 'SV': 'El Salvador', 'EE': 'Estonia', 'FI': 'Finland', 'FR': 'France', 'PF': 'French Polynesia', 'DE': 'Germany', 'GR': 'Greece', 'GP': 'Guadeloupe', 'GU': 'Guam', 'GT': 'Guatemala', 'HN': 'Honduras', 'HK': 'Hong Kong', 'HU': 'Hungary', 'IS': 'Iceland', 'IN': 'India', 'ID': 'Indonesia', 'IE': 'Ireland', 'IL': 'Israel', 'IT': 'Italy', 'JP': 'Japan', 'JO': 'Jordan', 'KW': 'Kuwait', 'LV': 'Latvia', 'LB': 'Lebanon', 'LI': 'Liechtenstein', 'LT': 'Lithuania', 'LU': 'Luxembourg', 'MY': 'Malaysia', 'MT': 'Malta', 'MX': 'Mexico', 'NL': 'Netherlands', 'NZ': 'New Zealand', 'NI': 'Nicaragua', 'NG': 'Nigeria', 'MP': 'Northern Mariana Islands', 'NO': 'Norway', 'OM': 'Oman', 'PA': 'Panama', 'PG': 'Papua New Guinea', 'PY': 'Paraguay', 'PE': 'Peru', 'PH': 'Philippines', 'PL': 'Poland', 'PT': 'Portugal', 'PR': 'Puerto Rico', 'QA': 'Qatar', 'RO': 'Romania', 'SA': 'Saudi Arabia', 'RS': 'Serbia', 'SG': 'Singapore', 'SK': 'Slovakia', 'SI': 'Slovenia', 'ZA': 'South Africa', 'ES': 'Spain', 'SE': 'Sweden', 'CH': 'Switzerland', 'TH': 'Thailand', 'TR': 'Turkey', 'TC': 'Turks and Caicos Islands', 'UA': 'Ukraine', 'AE': 'United Arab Emirates', 'GB': 'United Kingdom', 'US': 'United States', 'UY': 'Uruguay'}

STREAM_QUALITY_DICT = {"High": 2, "Medium": 1, "Low": 0}

STREAM_QUALITY_REVERSE_DICT = {2: "High", 1: "Medium", 0: "Low"}


SERVER = {
    "YT-DL-SERVER-1": "http://invidio.xamh.de",
    "YT-DL-SERVER-2": "http://ytprivate.com",
    "YT-DL-SERVER-3": "http://invidious.silkky.cloud",
    "YT-DL-SERVER-4": "http://invidious-us.kavin.rocks",
    "YT-DL-SERVER-5": "http://vid.puffyan.us",
}

SERVER_REVERSE = {
    "http://invidio.xamh.de": "YT-DL-SERVER-1",
    "http://ytprivate.com": "YT-DL-SERVER-2",
    "http://invidious.silkky.cloud": "YT-DL-SERVER-3",
    "http://invidious-us.kavin.rocks": "YT-DL-SERVER-4",
    "http://vid.puffyan.us": "YT-DL-SERVER-5",
}

EXPLORE = {"Trending": "trending", "Popular": "popular"}

EXPLORE_REVERSE = {"trending": "Trending", "popular": "Popular"}

SORT_BY = {"Relevance": "relevance", "Rating": "rating", "Upload date": "upload_date", "View count": "view_count"}
SORT_BY_REVERSE = {"relevance": "Relevance", "rating": "Rating", "upload_date": "Upload date", "view_count": "View count"}

AFTER_PLAYBACK = {"Loop Play": "loop_play", "Stop And Quit": "stop_and_quit"}
AFTER_PLAYBACK_REVERSE = {"loop_play": "Loop Play", "stop_and_quit": "Stop And Quit"}

