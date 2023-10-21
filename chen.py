import requests
from bs4 import BeautifulSoup
import pymysql
import openpyxl
from openpyxl.styles import Alignment
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('TkAgg')
import jieba
from wordcloud import WordCloud
import imageio
from pyecharts.charts import Map
from pyecharts import options as opts
from flask import Flask, render_template, request, redirect, make_response,session

connection = pymysql.Connect(
    host="127.0.0.1",
    port=3306,
    user="root",
    passwd="",
    db="cl",
    charset="utf8"
)


# 将字符串写进文件中，参数分别是文件名和内容
def writefile(file_name, content_str):
    with open(file_name, "w", encoding='utf-8', ) as f:
        f.write(content_str)
        f.close


# request url请求
def get_html_text(url):
    try:
        h = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/68.0.3440.106 Safari/537.36'
             }
        r = requests.get(url, headers=h, timeout=3000)
        r.raise_for_status()  # 如果不是200，则引发HTTPError异常
        r.encoding = r.apparent_encoding  # 根据内容去确定编码格式
        return r.text
    except BaseException as e:
        print("出现异常：", e)
        return str(e)


# 数据抓取及处理
def get_info():
    print("开始爬虫")
    url = "https://yz.chsi.com.cn/sch/?start="
    print("开始解析")
    data = []
    datalist = []
    all_data = []
    num = 1
    for page in range(0, 44):  # 43
        xurl = url + str(page * 20)
        html_text = get_html_text(xurl)
        # 数据抓取的文件保存
        all_text = ""
        all_text += xurl
        all_text += html_text
        x = str(xurl)
        writefile("./webapp/urltxt/"+ str(num) + ".txt", all_text)
        num += 1
        soup = BeautifulSoup(html_text, 'html.parser')
        datalist = []
        for i in soup.find_all('tr'):
            for j in i.find_all('td'):
                text = j.text.strip()
                text = str(text).replace("\ue664", "是")
                if text == '查看' or text == '查询' or text == '进入':
                    continue
                else:
                    data.append(text)
                    # print(data)
            if data == []:
                continue
            else:
                datalist.append(data)
                data = []
        fschool_name = []
        for z in soup.select(
                "body > div.main-wrapper > div.container > div.yxk-table > table > tbody > tr:nth-child(n) > td:nth-child(1) > a"):
            name = z.string.split()
            if name[0] == "/":
                continue
            fschool_name.append(name)
        j = 0
        for x in range(0, len(datalist)):
            datalist[x][0] = "".join(fschool_name[j])
            j = j + 1
        all_data += datalist
    # for i in range(0, len(all_data)):
    #     print(all_data[i])
    print("爬取完成")
    return all_data


def write_excel(file_name, list_content):
    wb = openpyxl.Workbook()  # 新建ExceL工作簿
    st = wb.active
    st['A1'] = "全国研究生院"  # 修改为自己的标题
    st['A1'].alignment = Alignment(horizontal='center', vertical='center')  # 居中
    second_row = ["院校名称", "所在地", "院校隶属", "研究生院", "自划线院校"]  # 根据实际情况写属性
    st.append(second_row)
    st.merge_cells("A1:E1")  # 根据实际情况合并单元格
    # print(len(list_content))
    for row in list_content:
        if row[3] == '':
            row[3] = '否'
        if row[4] == '':
            row[4] = '否'
        st.append(row)
        wb.save(file_name)  # 新工作簿的名称


def insert_sql(data):
    tup = tuple(data)
    cursor = connection.cursor()
    sql = "insert into fschool(院校名称,所在地,院校隶属,研究生院,自划线院校) values('%s','%s','%s','%s','%s')"
    for i in range(0, len(tup)):
        if tup[i][3] == '':
            tup[i][3] = '否'
        if tup[i][4] == '':
            tup[i][4] = '否'
        cursor.execute(sql % (tup[i][0], tup[i][1], tup[i][2], tup[i][3], tup[i][4]))


def select_sql_graduate_selfdrawn():
    cursor = connection.cursor()
    sql = "select count(院校名称) from fschool where 研究生院= '是'"
    cursor.execute(sql)
    T_graduate = cursor.fetchone()
    # print(int(T_graduate[0]),type(T_graduate))
    sql = "select count(院校名称) from fschool where 研究生院= '否'"
    cursor.execute(sql)
    F_graduate = cursor.fetchone()
    # print(int(F_graduate[0]), type(F_graduate))
    sql = "select count(院校名称) from fschool where 自划线院校= '是'"
    cursor.execute(sql)
    T_selfdrawn = cursor.fetchone()
    # print(int(T_selfdrawn[0]), type(T_selfdrawn))
    sql = "select count(院校名称) from fschool where 自划线院校= '否'"
    cursor.execute(sql)
    F_selfdrawn = cursor.fetchone()
    # print(int(F_selfdrawn[0]), type(F_selfdrawn))
    data_graself = [int(T_graduate[0]), int(F_graduate[0]), int(T_selfdrawn[0]), int(F_selfdrawn[0])]
    return data_graself


def create_matlab(data_graself):
    plt.rcParams['font.sans-serif'] = ['KaiTi']
    plt.title("研究生院和自划线院校分布图")
    plt.xlabel('研究生院和自划线院校')
    plt.ylabel('院校数')
    plt.ylim(0, 850)  # y轴取值，针对数值
    x = ['是研究生院', '不是研究生院', '是自划线院校', '不是自划线院校']  # ×轴的值
    y = data_graself  # y轴的值
    color = ["red", "blue", "brown", "orange"]
    plt.bar(x, y, color=color, width=0.25, linewidth=2.0, linestyle="--")
    # plt.show()  # 展示绘图
    plt.savefig('./webapp/static/image/研究生院和自划线院校分布图.png',  # ⽂件名：png、jpg、pdf
                dpi=100,  # 保存图⽚像素密度
                facecolor='white',  # 视图与边界之间颜⾊设置
                edgecolor='lightgreen',  # 视图边界颜⾊设置
                bbox_inches='tight')  # 保存图⽚完整


def create_worldwordcloud():
    cursor = connection.cursor()
    sql = "select 院校名称 from fschool"
    cursor.execute(sql)
    T_fschool = cursor.fetchall()
    T_fschool_text = ""
    for i in range(0, len(T_fschool)):
        T_fschool_text = T_fschool_text + ''.join(T_fschool[i]) + " "
    cut_text = jieba.cut(T_fschool_text)  # 结巴中文分词
    result = " ".join(cut_text)  # 分词结果空格连接
    mk1 = imageio.imread("./webapp/world.png")
    wc = WordCloud(
        # 中文需要设置字体，避免乱码，英文不必
        font_path=' ./fonts/simhei.ttf',
        background_color='white',  # 设置背景色
        width=500,  # 设置背景革
        height=500,  # 设置音景高
        max_font_size=100,  # 最大字体
        min_font_size=10,  # 最小字体
        mode='RGBA',  # coLormap= 'pink '
        mask=mk1  # 设置形状
    )
    wc.generate(result)  # 产生词云
    wc.to_file(r"./webapp/static/image/wordcloud.png")  # 保存图片
    plt.figure("研究生")  # 指定所绘图名称标题
    plt.imshow(wc)  # 以图片的形式显示词云
    plt.axis("off")  # 关闭图像坐标系
    # plt.show()


def map_visualmap(data, map_title) -> Map:
    c = (
        Map(opts.InitOpts(width='1200px', height='600px'))  # opts.InitOpts() 设置初始参数:width=画布宽,height=画布高
        .add(series_name="", data_pair=data, maptype="china")  # 系列名称(显示在中间的名称 )、数据 、地图类型
        .set_global_opts(
            title_opts=opts.TitleOpts(title=map_title),
            visualmap_opts=opts.VisualMapOpts(max_=160, min_=0),
        )
    )
    return c


def create_mapnum():
    cursor = connection.cursor()
    sql = "select 所在地,count(院校名称) from fschool group by 所在地"
    cursor.execute(sql)
    T_area = cursor.fetchall()
    # print(T_area)
    place = []
    num = []
    for i in range(0, len(T_area)):
        place.append(T_area[i][0])
        num.append(T_area[i][1])
    data = list(zip(place, num))
    map_title = "中国研究生高校分布"
    map = map_visualmap(data, map_title)
    map.render(path='./webapp/static/image/map.html')


def index_data():
    cursor=connection.cursor()
    sql='SELECT `所在地`,COUNT(`院校名称`) as num from fschool GROUP BY `所在地` ORDER BY num desc limit 0,6'
    cursor.execute(sql)
    data=cursor.fetchall()
    # area=[]
    # num=[]
    datazip=[]
    for i in range(0,len(data)):
        # area.append(data[i][0])
        # num.append(str(data[i][1]))
        d=dict(address=data[i][0],number=str(data[i][1]))
        datazip.append(d)
    # print(datazip)
    return datazip

def mains():
    # 主函数
    # 爬取信息并处理
    data = get_info()
    # #存储进表格
    write_excel('./webapp/test1.xlsx', data)
    # 存储到数据库
    insert_sql(data)
    data_graself = select_sql_graduate_selfdrawn()
    create_matlab(data_graself)
    create_worldwordcloud()
    create_mapnum()


# 网页部分
app = Flask(__name__)
# 配置 SELECT_KEY
app.config['SECRET_KEY'] = '3c2d9d261a464e4e8814c5a39aa72f1c'

@app.route('/')
@app.route('/index')
def index():
    # mains()
    session.pop('username', None)
    return render_template("login.html",title="登录")

@app.route('/login',methods=['GET'])
def login():
    if request.method=='GET':
        username = request.args.get('username', '用户名不存在')
        password = request.args.get('password', '密码不存在')
        cursor = connection.cursor()
        sql = "select username from users where username='%s' and password='%s'"
        cursor.execute(sql % (username, password))
        username = cursor.fetchone()
        datazip = index_data()
        # 判断是否已经在登录状态上:判断session中是否有uname的值
        if 'username' in session:
            return render_template('login.html',title="中国研究生高校数据分析", datazip=datazip, username=str(username[0]))
        else:
            if (username == None):
                return render_template("login.html", title="登录")
            else:
                session['username'] = str(username[0])
                return render_template("index.html", title="中国研究生高校数据分析", datazip=datazip, username=str(username[0]))


@app.route('/to_register',methods=['GET'])
def to_register():
    if request.method == 'GET':
        return render_template("register.html")

@app.route('/post_register',methods=['GET'])
def register():
    if request.method=='GET':
        username=request.args.get('username','用户名不存在')
        password=request.args.get('password','密码不存在')
        password_twice=request.args.get('password_twice','密码不存在')
        if password_twice==password:
            cursor = connection.cursor()
            sql = "insert into users(username,password) values('%s','%s')"
            cursor.execute(sql%(username,password))
            return render_template("login.html", title="登录")
        else:
            return render_template("register.html")

@app.route("/search_fschool")
def search():
    # 判断是否已经在登录状态上:判断session中是否有uname的值
    if 'username' in session:
        # 已经登录了，直接去往首页
        return render_template("search_fschool.html")
    else:
        return render_template('login.html')

@app.route("/search_result_place",methods=['GET'])
def search_result_place():
    if request.method=='GET':
        # 判断是否已经在登录状态上:判断session中是否有uname的值
        if 'username' in session:
            # 已经登录了，直接去往首页
            school = request.args.get('school')
            cursor = connection.cursor()
            sql = "select 所在地 from fschool where 院校名称='%s'"
            cursor.execute(sql % school)
            relt = cursor.fetchall()
            data = str(relt[0][0])
            # print(data)
            return render_template("result.html", result=data, status="1")
        else:
            return render_template('login.html')


@app.route("/search_result_more",methods=['GET'])
def search_result_more():
    if request.method=='GET':
        # 判断是否已经在登录状态上:判断session中是否有uname的值
        if 'username' in session:
            # 已经登录了，直接去往首页
            place = request.args.get('place')
            cursor = connection.cursor()
            sql = "select 院校名称,院校隶属,研究生院,自划线院校 from fschool where 所在地='%s'"
            cursor.execute(sql % place)
            more = cursor.fetchall()
            datazip = []
            for i in range(0, len(more)):
                d = dict(school_name=more[i][0], school_belongs=str(more[i][1]), school_graduate=str(more[i][2]),
                         school_self=str(more[i][3]), )
                datazip.append(d)
            return render_template("result.html", datazip=datazip, status="2", place=place)
        else:
            return render_template('login.html')

if __name__ == '__main__':
    # app.run()
    app.run(host='127.0.0.1', port=88, debug=True)
