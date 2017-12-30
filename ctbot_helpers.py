'''
Helper functions moved here to clean up main script and increase readability
'''
from keys import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_TO, EMAIL_FROM
from email.mime.text import MIMEText
import datetime, time
import smtplib


def send_email(subject, message):

    date_string = datetime.datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

    msg = MIMEText(message)
    msg['Subject'] = "{} {}".format(subject, date_string)
    msg['To'] = ", ".join(EMAIL_TO)
    msg['From'] = EMAIL_FROM
    mail = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    mail.starttls()
    mail.login(SMTP_USERNAME, SMTP_PASSWORD)
    mail.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
    mail.quit()


def init_variables():
    variables = {
            #Live toggle
            'live': False,
            #Currency pair
            'pair': '',
            
            # Periods used. All available on Poloniex except 24h
            # 5m, 15m, 30m, 2h, 4h
            'periods': [300, 900, 1800, 7200, 14400],

            # Each period has its own variables
            300: {
                        'all_candles': list(),
                        'len_candles': 0,

                        'all_dates': list(),

                        'all_close_prices': list(),

                        'all_rsi': list(),
                        'all_rsi_d': list(),
                        'all_rsi_u': list(),

                        'all_macd': list(),
                        'all_macd_signal': list(),
                        'all_macd_hist': list(),

                        'all_bollinger': list(),

                        'all_score': list(),
                        'all_rsi_score': list(),
                        'all_macd_score': list()
            },
            900: {
                        'all_candles': list(),
                        'len_candles': 0,

                        'all_dates': list(),

                        'all_close_prices': list(),

                        'all_rsi': list(),
                        'all_rsi_d': list(),
                        'all_rsi_u': list(),

                        'all_macd': list(),
                        'all_macd_signal': list(),
                        'all_macd_hist': list(),

                        'all_bollinger': list(),

                        'all_score': list(),
                        'all_rsi_score': list(),
                        'all_macd_score': list()
            },
            1800: {
                        'all_candles': list(),
                        'len_candles': 0,

                        'all_dates': list(),

                        'all_close_prices': list(),

                        'all_rsi': list(),
                        'all_rsi_d': list(),
                        'all_rsi_u': list(),

                        'all_macd': list(),
                        'all_macd_signal': list(),
                        'all_macd_hist': list(),

                        'all_bollinger': list(),

                        'all_score': list(),
                        'all_rsi_score': list(),
                        'all_macd_score': list()
            },
            7200: {
                        'all_candles': list(),
                        'len_candles': 0,

                        'all_dates': list(),

                        'all_close_prices': list(),

                        'all_rsi': list(),
                        'all_rsi_d': list(),
                        'all_rsi_u': list(),

                        'all_macd': list(),
                        'all_macd_signal': list(),
                        'all_macd_hist': list(),

                        'all_bollinger': list(),

                        'all_score': list(),
                        'all_rsi_score': list(),
                        'all_macd_score': list()
            },
            14400: {
                        'all_candles': list(),
                        'len_candles': 0,

                        'all_dates': list(),

                        'all_close_prices': list(),

                        'all_rsi': list(),
                        'all_rsi_d': list(),
                        'all_rsi_u': list(),

                        'all_macd': list(),
                        'all_macd_signal': list(),
                        'all_macd_hist': list(),

                        'all_bollinger': list(),

                        'all_score': list(),
                        'all_rsi_score': list(),
                        'all_macd_score': list()
            },

            #Starting with 1 coin and 0 USDT
            'coins': 1,
            'usdt': 0,

            #Trade details
            'active_trade': False,
            'active_trade_price': 0,
            'current_trade_details': dict(),
            'plot_buys': list(),
            'plot_sells': list(),
    }
    return variables