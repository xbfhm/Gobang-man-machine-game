# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.core.window import Window
from kivy.resources import resource_add_path
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


# ==========================
# 中文字体
# ==========================

# 把字体文件放到程序同目录
# 推荐 NotoSansCJK-Regular.ttc

LabelBase.register(
    name="Chinese",
    fn_regular="NotoSansCJK-Regular.ttc"
)



# ==========================
# 游戏参数
# ==========================

BOARD_SIZE = 19

EMPTY = 0
PLAYER = 1
AI = 2


# AI难度
AI_LEVEL = "中"



# ==========================
# 胜负判断
# ==========================

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



# ==========================
# AI评分
# ==========================


PATTERN_SCORES={

    "win":100000,

    "open4":10000,

    "four":3000,

    "open3":1000,

    "three":300,

    "two":100

}



def line_score(cells):

    s="".join(cells)

    score=0


    if "OOOOO" in s:
        score+=PATTERN_SCORES["win"]


    if ".OOOO." in s:
        score+=PATTERN_SCORES["open4"]


    if (
        "OOOO." in s
        or
        ".OOOO" in s
    ):
        score+=PATTERN_SCORES["four"]


    if ".OOO." in s:
        score+=PATTERN_SCORES["open3"]


    if (
        "OOO." in s
        or
        ".OOO" in s
    ):
        score+=PATTERN_SCORES["three"]


    if ".OO." in s:
        score+=PATTERN_SCORES["two"]


    return score





def evaluate_point(board,row,col,who):

    opponent = (
        PLAYER
        if who==AI
        else AI
    )


    def get_line(dr,dc,target):

        cells=[]


        for i in range(-4,5):

            r=row+dr*i
            c=col+dc*i


            if (
                0<=r<BOARD_SIZE
                and
                0<=c<BOARD_SIZE
            ):

                if i==0:
                    cells.append("O")

                elif board[r][c]==target:
                    cells.append("O")

                elif board[r][c]==EMPTY:
                    cells.append(".")


                else:
                    cells.append("X")

            else:
                cells.append("X")


        return cells



    total=0


    for dr,dc in [
        (1,0),
        (0,1),
        (1,1),
        (1,-1)
    ]:

        #进攻

        total+=line_score(
            get_line(dr,dc,who)
        )


        #防守

        total+=int(
            line_score(
                get_line(dr,dc,opponent)
            )
            *
            0.9
        )


    return total





# ==========================
# 候选位置
# ==========================


def candidate_moves(board):

    result=set()

    has=False


    for r in range(BOARD_SIZE):

        for c in range(BOARD_SIZE):

            if board[r][c]!=EMPTY:

                has=True


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
                            result.add(
                                (nr,nc)
                            )


    if not has:
        return [
            (
                BOARD_SIZE//2,
                BOARD_SIZE//2
            )
        ]


    return list(result)





# ==========================
# AI走棋
# ==========================


def ai_move(board):


    moves=candidate_moves(board)



    # 低难度
    if AI_LEVEL=="低":

        return random.choice(moves)



    # 高难度：先检查必胜

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



        # 防止玩家赢


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




    # 中/高评分


    best=-1
    pos=None


    for r,c in moves:

        score=evaluate_point(
            board,
            r,
            c,
            AI
        )


        if score>best:

            best=score
            pos=(r,c)


    return pos
# ==========================
# 棋盘控件
# ==========================

class BoardWidget(Widget):

    def __init__(self,status_label,**kwargs):

        super().__init__(**kwargs)

        self.status_label=status_label

        self.board=[
            [EMPTY]*BOARD_SIZE
            for _ in range(BOARD_SIZE)
        ]

        self.move_history=[]

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



    # 棋盘原点

    def grid_origin(self):

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

        ox,oy=self.grid_origin()


        with self.canvas:


            # 棋盘颜色

            Color(
                0.85,
                0.7,
                0.45,
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

                    v=self.board[r][c]


                    if v==EMPTY:
                        continue


                    x=ox+c*cs
                    y=oy+r*cs


                    radius=cs*0.4



                    if v==PLAYER:

                        Color(
                            0.05,
                            0.05,
                            0.05,
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



            # 获胜高亮

            if self.winning_cells:


                Color(
                    1,
                    0.82,
                    0.1,
                    1
                )


                for r,c in self.winning_cells:


                    x=ox+c*cs
                    y=oy+r*cs


                    Line(
                        circle=(
                            x,
                            y,
                            cs*0.48
                        ),
                        width=2.5
                    )





    # 点击棋盘

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

        ox,oy=self.grid_origin()



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



        # 玩家落子

        self.board[row][col]=PLAYER


        self.move_history.append(
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



        if self.is_full():

            self.finish_game(
                None,
                None
            )

            return



        self.set_status(
            "AI思考中...",
            (1,1,1,1)
        )


        self.awaiting_ai=True



        self.ai_event=Clock.schedule_once(
            self.do_ai_move,
            0.4
        )





    # AI落子

    def do_ai_move(self,dt):

        self.awaiting_ai=False

        pos=ai_move(
            self.board
        )


        if pos is None:
            return


        r,c=pos


        self.board[r][c]=AI


        self.move_history.append(
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




    def is_full(self):

        return all(
            self.board[r][c]!=EMPTY
            for r in range(BOARD_SIZE)
            for c in range(BOARD_SIZE)
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

    def retract_last(self):

        if not self.awaiting_ai:

            return


        if self.ai_event:

            self.ai_event.cancel()


        if self.move_history:

            r,c,w=self.move_history.pop()

            self.board[r][c]=EMPTY


        self.awaiting_ai=False

        self.redraw()


        self.set_status(
            "轮到你了（黑棋）",
            (1,1,1,1)
        )





    # 悔棋

    def undo_move(self):

        if len(self.move_history)<2:

            return



        for _ in range(2):

            r,c,w=self.move_history.pop()

            self.board[r][c]=EMPTY



        self.game_over=False

        self.winning_cells=None


        self.redraw()


        self.set_status(
            "悔棋成功",
            (1,1,1,1)
        )





    # 重置

    def reset(self):

        self.board=[
            [EMPTY]*BOARD_SIZE
            for _ in range(BOARD_SIZE)
        ]

        self.move_history=[]

        self.game_over=False

        self.winning_cells=None

        self.awaiting_ai=False


        self.redraw()


        self.set_status(
            "轮到你了（黑棋）",
            (1,1,1,1)
        )    # ==========================
# 按钮样式
# ==========================

def flat_button(text,color):

    return Button(
        text=text,
        font_name="Chinese",
        background_normal="",
        background_color=color,
        color=(1,1,1,1),
        font_size=16
    )



# ==========================
# 主程序
# ==========================

class GomokuApp(App):


    def build(self):

        global AI_LEVEL


        Window.clearcolor=(
            0.1,
            0.1,
            0.12,
            1
        )



        root=BoxLayout(
            orientation="vertical",
            padding=10,
            spacing=8
        )



        # 标题

        title=Label(

            text="五子棋人机对战",

            font_name="Chinese",

            font_size=25,

            size_hint=(1,0.07),

            color=(
                1,
                0.85,
                0.4,
                1
            )
        )



        # 状态

        status=Label(

            text="轮到你了（黑棋）",

            font_name="Chinese",

            font_size=18,

            size_hint=(1,0.06)

        )



        # 棋盘

        board=BoardWidget(
            status,
            size_hint=(1,0.80)
        )



        # =====================
        # 弹窗
        # =====================


        def show_result(winner):


            if winner==PLAYER:

                msg="恭喜，你赢了！"

                title="胜利"


            elif winner==AI:

                msg="AI赢了，再挑战一次吧"

                title="失败"


            else:

                msg="双方打平"

                title="平局"




            box=BoxLayout(
                orientation="vertical",
                spacing=10,
                padding=10
            )



            label=Label(

                text=msg,

                font_name="Chinese",

                font_size=18
            )


            btn=flat_button(

                "重新开始",

                (
                    0.2,
                    0.6,
                    0.3,
                    1
                )

            )


            box.add_widget(label)

            box.add_widget(btn)



            popup=Popup(

                title=title,

                content=box,

                size_hint=(
                    0.8,
                    0.35
                )
            )



            btn.bind(
                on_release=lambda x:
                (
                    board.reset(),
                    popup.dismiss()
                )
            )


            popup.open()




        board.on_win_callback=show_result





        # =====================
        # 底部按钮
        # =====================


        row=BoxLayout(

            size_hint=(1,0.07),

            spacing=5

        )



        undo=flat_button(

            "悔棋",

            (
                0.3,
                0.4,
                0.7,
                1
            )
        )



        retract=flat_button(

            "撤回",

            (
                0.5,
                0.5,
                0.25,
                1
            )
        )



        restart=flat_button(

            "重新开始",

            (
                0.6,
                0.3,
                0.3,
                1
            )
        )



        level=flat_button(

            "难度：中",

            (
                0.4,
                0.4,
                0.5,
                1
            )
        )




        # 难度循环

        def change_level(*args):

            global AI_LEVEL


            levels=[
                "低",
                "中",
                "高"
            ]


            index=levels.index(
                AI_LEVEL
            )


            index+=1


            if index>=3:

                index=0



            AI_LEVEL=levels[index]


            level.text="难度："+AI_LEVEL




        level.bind(
            on_release=change_level
        )



        undo.bind(
            on_release=lambda x:
            board.undo_move()
        )


        retract.bind(
            on_release=lambda x:
            board.retract_last()
        )


        restart.bind(
            on_release=lambda x:
            board.reset()
        )



        row.add_widget(undo)

        row.add_widget(retract)

        row.add_widget(level)

        row.add_widget(restart)



        root.add_widget(title)

        root.add_widget(status)

        root.add_widget(board)

        root.add_widget(row)



        return root




# ==========================
# 启动
# ==========================

if __name__=="__main__":

    GomokuApp().run()
