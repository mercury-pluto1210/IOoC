from datetime import datetime

# Twitter APIから取得したcreated_atを整える関数
# .astimezone()によって日本時間に整形
def make_convert_date_format(src_format, dst_format):
  def convert_date_format(s):
    return  datetime.strftime(
              datetime.strptime(
                s, src_format
              ).astimezone(),
            dst_format
    )

  return convert_date_format

convert_date_format = make_convert_date_format(
  '%a %b %d %H:%M:%S %z %Y', '%Y-%m-%d'
)