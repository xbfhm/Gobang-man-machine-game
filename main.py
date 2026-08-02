# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.core.window import Window
from kivy.core.text import LabelBase

from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup

from kivy.graphics import (
    Color,
    Line,
    Ellipse,
    Rectangle
)

from kivy.clock import Clock

import random


# =========================
# 中文字体 (.otf)
# =========================

LabelBase.register(
    name="Chinese",
    fn_regular="NotoSansCJK-Regular.otf"
)



# =========================
# 游戏设置
# =========================

BOARD_SIZE = 19

EMPTY = 0
PLAYER = 1
AI = 2


# 当前难度
AI_LEVEL = "中"



# =========================
# 判断胜利
# =========================

def check_win(board,row,col,who):

    directions=[
        (1,0),
        (0,1),
        (1,1),
        (1,-1)
    ]


    for dr,dc in directions:

        cells=[
            (row,col)
        ]


        # 正方向

        r=row+dr
        c=col+dc

        while (
            0<=r<BOARD_SIZE
            and
            0<=c<BOARD_SIZE
            and
            board[r][c]==who
        ):

            cells.append((r,c))

            r+=dr
            c+=dc



        # 反方向

        r=row-dr
        c=col-dc


        while (
            0<=r<BOARD_SIZE
            and
            0<=c<BOARD_SIZE
            and
            board[r][c]==who
        ):

            cells.append((r,c))

            r-=dr
            c-=dc



        if len(cells)>=5:

            return True,cells



    return False,None




# =========================
# AI棋型评分
# =========================


SCORES={

    "FIVE":100000,

    "OPEN4":10000,

    "FOUR":3000,

    "OPEN3":1000,

    "THREE":300,

    "TWO":100

}



def pattern_score(cells):

    s="".join(cells)

    score=0



    if "OOOOO" in s:

        score+=SCORES["FIVE"]



    if ".OOOO." in s:

        score+=SCORES["OPEN4"]



    if (
        "OOOO." in s
        or
        ".OOOO" in s
    ):

        score+=SCORES["FOUR"]



    if ".OOO." in s:

        score+=SCORES["OPEN3"]



    if (
        "OOO." in s
        or
        ".OOO" in s
    ):

        score+=SCORES["THREE"]



    if ".OO." in s:

        score+=SCORES["TWO"]



    return score





def evaluate(board,row,col,who):

    enemy = PLAYER if who==AI else AI


    total=0



    def get_line(dr,dc,target):

        result=[]


        for i in range(-4,5):

            r=row+dr*i
            c=col+dc*i



            if (
                0<=r<BOARD_SIZE
                and
                0<=c<BOARD_SIZE
            ):


                if i==0:

                    result.append("O")

                elif board[r][c]==target:

                    result.append("O")

                elif board[r][c]==EMPTY:

                    result.append(".")


                else:

                    result.append("X")

            else:

                result.append("X")



        return result



    for dr,dc in [
        (1,0),
        (0,1),
        (1,1),
        (1,-1)
    ]:

        # 自己进攻

        total+=pattern_score(
            get_line(dr,dc,who)
        )


        # 防守

        total+=int(
            pattern_score(
                get_line(dr,dc,enemy)
            )
            *
            0.9
        )



    return total




# =========================
# 搜索附近位置
# =========================


def candidate_moves(board):

    moves=set()

    exist=False


    for r in range(BOARD_SIZE):

        for c in range(BOARD_SIZE):

            if board[r][c]!=EMPTY:

                exist=True


                for dr in range(-2,3):

                    for dc in range(-2,3):

                        nr=r+dr
                        nc=c+dc


                        if (
                            0<=nr<BOARD_SIZE
                            and
                            0<=nc<BOARD_SIZE
                            and
                            board[nr][nc]==EMPTY
                        ):

                            moves.add(
                                (nr,nc)
                            )



    if not exist:

        return [
            (
                BOARD_SIZE//2,
                BOARD_SIZE//2
            )
        ]


    return list(moves)





# =========================
# AI落子
# =========================


def ai_move(board):

    moves=candidate_moves(board)



    # 低难度

    if AI_LEVEL=="低":

        return random.choice(moves)




    # 高难度
    # 先赢，再堵


    if AI_LEVEL=="高":


        for r,c in moves:

            board[r][c]=AI

            win,_=check_win(
                board,
                r,
                c,
                AI
            )

            board[r][c]=EMPTY


            if win:

                return r,c



        for r,c in moves:

            board[r][c]=PLAYER

            win,_=check_win(
                board,
                r,
                c,
                PLAYER
            )

            board[r][c]=EMPTY


            if win:

                return r,c




    best=-1

    result=None



    for r,c in moves:

        score=evaluate(
            board,
            r,
            c,
            AI
        )


        if score>best:

            best=score

            result=(r,c)



    return result


# =========================
# 棋盘 Widget
# =========================

class BoardWidget(Widget):

    def __init__(self,status_label,**kwargs):

        super().__init__(**kwargs)

        self.status_label=status_label


        self.board=[
            [EMPTY]*BOARD_SIZE
            for _ in range(BOARD_SIZE)
        ]


        self.history=[]


        self.last_move=None


        self.winning_cells=None


        self.game_over=False


        self.awaiting_ai=False


        self.ai_event=None


        self.on_win_callback=None



        self.bind(
            size=self.redraw,
            pos=self.redraw
        )



    # 棋格大小

    def cell_size(self):

        return min(
            self.width,
            self.height
        )/(BOARD_SIZE+1)




    # 棋盘坐标

    def origin(self):

        cs=self.cell_size()

        ox=self.x+(
            self.width-cs*(BOARD_SIZE-1)
        )/2


        oy=self.y+(
            self.height-cs*(BOARD_SIZE-1)
        )/2


        return ox,oy




    # 绘制

    def redraw(self,*args):

        self.canvas.clear()


        cs=self.cell_size()

        ox,oy=self.origin()



        with self.canvas:



            # 背景

            Color(
                0.86,
                0.72,
                0.48,
                1
            )


            Rectangle(
                pos=self.pos,
                size=self.size
            )



            # 棋盘线

            Color(
                0.2,
                0.15,
                0.1,
                1
            )


            for i in range(BOARD_SIZE):


                Line(
                    points=[
                        ox+i*cs,
                        oy,
                        ox+i*cs,
                        oy+cs*(BOARD_SIZE-1)
                    ],
                    width=1
                )



                Line(
                    points=[
                        ox,
                        oy+i*cs,
                        ox+cs*(BOARD_SIZE-1),
                        oy+i*cs
                    ],
                    width=1
                )




            # 棋子

            for r in range(BOARD_SIZE):

                for c in range(BOARD_SIZE):


                    if self.board[r][c]==EMPTY:

                        continue



                    x=ox+c*cs
                    y=oy+r*cs


                    radius=cs*0.4



                    if self.board[r][c]==PLAYER:


                        Color(
                            0.03,
                            0.03,
                            0.03,
                            1
                        )


                    else:


                        Color(
                            0.95,
                            0.95,
                            0.95,
                            1
                        )



                    Ellipse(
                        pos=(
                            x-radius,
                            y-radius
                        ),
                        size=(
                            radius*2,
                            radius*2
                        )
                    )




            # 最后一步标记

            if self.last_move:


                r,c=self.last_move


                Color(
                    1,
                    0,
                    0,
                    1
                )


                Line(
                    circle=(
                        ox+c*cs,
                        oy+r*cs,
                        cs*0.15
                    ),
                    width=2
                )




            # 五连高亮

            if self.winning_cells:


                Color(
                    1,
                    0.8,
                    0,
                    1
                )


                for r,c in self.winning_cells:


                    Line(
                        circle=(
                            ox+c*cs,
                            oy+r*cs,
                            cs*0.48
                        ),
                        width=3
                    )






    # 点击下棋

    def on_touch_down(self,touch):


        if (
            self.game_over
            or
            self.awaiting_ai
            or
            not self.collide_point(*touch.pos)
        ):
            return



        cs=self.cell_size()

        ox,oy=self.origin()



        col=round(
            (touch.x-ox)/cs
        )


        row=round(
            (touch.y-oy)/cs
        )



        if not(
            0<=row<BOARD_SIZE
            and
            0<=col<BOARD_SIZE
        ):

            return



        if self.board[row][col]!=EMPTY:

            return



        # 玩家棋

        self.board[row][col]=PLAYER

        self.last_move=(row,col)


        self.history.append(
            (row,col,PLAYER)
        )


        self.redraw()



        win,cells=check_win(
            self.board,
            row,
            col,
            PLAYER
        )



        if win:

            self.finish_game(
                PLAYER,
                cells
            )

            return



        self.awaiting_ai=True


        self.set_status(
            "AI思考中...",
            (1,1,1,1)
        )


        self.ai_event=Clock.schedule_once(
            self.ai_play,
            0.4
        )





    # AI下棋

    def ai_play(self,dt):


        self.awaiting_ai=False


        pos=ai_move(
            self.board
        )


        if not pos:

            return



        r,c=pos


        self.board[r][c]=AI


        self.last_move=(r,c)


        self.history.append(
            (r,c,AI)
        )


        self.redraw()



        win,cells=check_win(
            self.board,
            r,
            c,
            AI
        )


        if win:

            self.finish_game(
                AI,
                cells
            )

            return



        self.set_status(
            "轮到你了（黑棋）",
            (1,1,1,1)
        )





    def set_status(self,text,color):

        self.status_label.text=text

        self.status_label.color=color





    def finish_game(self,winner,cells):


        self.game_over=True

        self.winning_cells=cells


        self.redraw()



        if winner==PLAYER:

            self.set_status(
                "你赢了！",
                (0.3,1,0.3,1)
            )


        elif winner==AI:

            self.set_status(
                "AI赢了",
                (1,0.3,0.3,1)
            )


        else:

            self.set_status(
                "平局",
                (1,1,0.3,1)
            )



        if self.on_win_callback:

            self.on_win_callback(winner)






    # 撤回

    def retract(self):


        if not self.awaiting_ai:

            return



        if self.ai_event:

            self.ai_event.cancel()



        if self.history:


            r,c,w=self.history.pop()

            self.board[r][c]=EMPTY



        self.awaiting_ai=False

        self.last_move=None


        self.redraw()





    # 悔棋

    def undo(self):


        if len(self.history)<2:

            return



        for i in range(2):

            r,c,w=self.history.pop()

            self.board[r][c]=EMPTY



        self.last_move=None

        self.game_over=False

        self.winning_cells=None


        self.redraw()





    # 重开

    def reset(self):


        self.board=[
            [EMPTY]*BOARD_SIZE
            for _ in range(BOARD_SIZE)
        ]


        self.history=[]

        self.last_move=None

        self.game_over=False

        self.winning_cells=None


        self.redraw()


        self.set_status(
            "轮到你了（黑棋）",
            (1,1,1,1)
        )   


# =========================
# 按钮样式（调大字体至 24）
# =========================

def make_button(text):

    return Button(
        text=text,
        font_name="Chinese",
        font_size=24,  # 原为 16 -> 调整为 24
        background_normal="",
        background_color=(
            0.25,
            0.45,
            0.7,
            1
        )
    )





# =========================
# 主程序
# =========================


class GomokuApp(App):


    def build(self):

        global AI_LEVEL


        Window.clearcolor=(
            0.08,
            0.08,
            0.1,
            1
        )



        root=BoxLayout(
            orientation="vertical",
            padding=10,
            spacing=8
        )



        title=Label(

            text="五子棋人机对战",

            font_name="Chinese",

            font_size=36,  # 原为 26 -> 调整为 36

            size_hint=(
                1,
                0.08
            ),

            color=(
                1,
                0.85,
                0.4,
                1
            )
        )



        status=Label(

            text="轮到你了（黑棋）",

            font_name="Chinese",

            font_size=26,  # 原为 18 -> 调整为 26

            size_hint=(
                1,
                0.06
            )
        )



        # 难度显示

        level_label=Label(

            text="难度：中",

            font_name="Chinese",

            font_size=24,  # 原为 17 -> 调整为 24

            size_hint=(
                1,
                0.05
            )
        )



        board=BoardWidget(
            status,
            size_hint=(
                1,
                0.60  # 稍微缩小棋盘占比(0.68->0.60)，为下方大字按钮预留空间
            )
        )




        # 胜利弹窗

        def result_popup(winner):


            if winner==PLAYER:

                msg="恭喜，你赢了！"


            elif winner==AI:

                msg="AI赢了，再挑战一次吧"


            else:

                msg="平局"




            box=BoxLayout(

                orientation="vertical",

                spacing=10

            )



            box.add_widget(
                Label(
                    text=msg,
                    font_name="Chinese",
                    font_size=26  # 原为 18 -> 调整为 26
                )
            )


            close=make_button(
                "确定"
            )


            box.add_widget(close)



            pop=Popup(

                title="游戏结束",

                title_size=24,  # 添加标题字号设置

                content=box,

                size_hint=(
                    0.7,
                    0.4  # 稍微增大弹窗尺寸以容纳大字体
                )

            )



            close.bind(
                on_release=pop.dismiss
            )


            pop.open()




        board.on_win_callback=result_popup





        # 难度按钮

        level_box=BoxLayout(

            size_hint=(
                1,
                0.10  # 稍微调高占比以容纳大字按钮
            ),

            spacing=5

        )



        def set_level(level):

            global AI_LEVEL

            AI_LEVEL=level

            level_label.text="难度："+level




        low=make_button("低")

        mid=make_button("中")

        high=make_button("高")



        low.bind(
            on_release=lambda x:set_level("低")
        )


        mid.bind(
            on_release=lambda x:set_level("中")
        )


        high.bind(
            on_release=lambda x:set_level("高")
        )



        level_box.add_widget(low)

        level_box.add_widget(mid)

        level_box.add_widget(high)






        # 功能按钮

        button_box=BoxLayout(

            size_hint=(
                1,
                0.11  # 稍微调高占比以容纳大字按钮
            ),

            spacing=6

        )



        undo=make_button(
            "悔棋"
        )


        retract=make_button(
            "撤回"
        )


        restart=make_button(
            "重新开始"
        )



        undo.bind(
            on_release=lambda x:board.undo()
        )


        retract.bind(
            on_release=lambda x:board.retract()
        )


        restart.bind(
            on_release=lambda x:board.reset()
        )



        button_box.add_widget(
            undo
        )

        button_box.add_widget(
            retract
        )

        button_box.add_widget(
            restart
        )





        root.add_widget(title)

        root.add_widget(status)

        root.add_widget(level_label)

        root.add_widget(board)

        root.add_widget(level_box)

        root.add_widget(button_box)



        return root





if __name__=="__main__":

    GomokuApp().run()
