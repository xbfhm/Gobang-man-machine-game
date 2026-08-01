# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.core.window import Window

from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup

from kivy.graphics import Color, Line, Ellipse, Rectangle
from kivy.clock import Clock

import random


# ==========================
# 游戏设置
# ==========================

BOARD_SIZE = 19

EMPTY = 0
PLAYER = 1
AI = 2


# AI难度
AI_LEVEL = "中"



# ==========================
# 判断胜利
# ==========================

def check_win(board,row,col,who):

    directions = [
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

SCORES={

    "five":100000,

    "four":10000,

    "three":1000,

    "two":100

}




def line_score(cells):

    s="".join(cells)

    score=0


    if "OOOOO" in s:

        score+=SCORES["five"]


    if (
        ".OOOO." in s
        or
        "OOOO." in s
        or
        ".OOOO" in s
    ):

        score+=SCORES["four"]



    if (
        ".OOO." in s
        or
        ".OOO" in s
        or
        "OOO."
        in s
    ):

        score+=SCORES["three"]



    if ".OO." in s:

        score+=SCORES["two"]


    return score






def evaluate_point(board,row,col,who):

    enemy = PLAYER if who==AI else AI


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


        total += line_score(
            get_line(dr,dc,who)
        )


        total += int(
            line_score(
                get_line(dr,dc,enemy)
            )
            *0.9
        )


    return total






# ==========================
# 搜索附近位置
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


    # 简单模式随机

    if AI_LEVEL=="低":

        return random.choice(moves)



    # 高难度先判断胜负

    if AI_LEVEL=="高":


        # AI能赢直接赢

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




        # 阻止玩家

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
    best_pos=None


    for r,c in moves:


        score=evaluate_point(
            board,
            r,
            c,
            AI
        )


        if score>best:

            best=score

                      best_pos=(r,c)



    return best_pos
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



    def cell_size(self):

        return min(
            self.width,
            self.height
        )/(BOARD_SIZE+1)



    def grid_origin(self):

        cs=self.cell_size()

        ox=self.x+(
            self.width-cs*(BOARD_SIZE-1)
        )/2

        oy=self.y+(
            self.height-cs*(BOARD_SIZE-1)
        )/2

        return ox,oy




    # ======================
    # 绘制棋盘
    # ======================

    def redraw(self,*args):

        self.canvas.clear()

        cs=self.cell_size()

        ox,oy=self.grid_origin()


        with self.canvas:


            # 背景

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

                    value=self.board[r][c]


                    if value==EMPTY:

                        continue



                    x=ox+c*cs
                    y=oy+r*cs


                    radius=cs*0.4



                    if value==PLAYER:

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




            # 胜利高亮

            if self.winning_cells:


                Color(
                    1,
                    0.8,
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






    # ======================
    # 玩家落子
    # ======================

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



        self.set_status(
            "AI思考中...",
            (1,1,1,1)
        )


        self.awaiting_ai=True


        self.ai_event=Clock.schedule_once(
            self.do_ai_move,
            0.4
        )





    # ======================
    # AI落子
    # ======================

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
        ) 
        # ==========================
# 按钮样式
# ==========================

def flat_button(text,color):

    return Button(
        text=text,
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



        title=Label(
            text="五子棋人机对战",
            font_size=25,
            size_hint=(1,0.07),
            color=(
                1,
                0.85,
                0.4,
                1
            )
        )



        status=Label(
            text="轮到你了（黑棋）",
            font_size=18,
            size_hint=(1,0.06)
        )



        board=BoardWidget(
            status,
            size_hint=(1,0.80)
        )



        # ======================
        # 胜利弹窗
        # ======================

        def show_result(winner):

            if winner==PLAYER:

                title_text="胜利"

                msg="恭喜，你赢了！"


            elif winner==AI:

                title_text="失败"

                msg="AI赢了，再挑战一次吧"


            else:

                title_text="平局"

                msg="双方打平"



            box=BoxLayout(
                orientation="vertical",
                spacing=10,
                padding=10
            )


            label=Label(
                text=msg,
                font_size=18
            )


            again=flat_button(
                "重新开始",
                (
                    0.2,
                    0.6,
                    0.3,
                    1
                )
            )


            box.add_widget(label)

            box.add_widget(again)



            popup=Popup(
                title=title_text,
                content=box,
                size_hint=(
                    0.8,
                    0.35
                )
            )


            again.bind(
                on_release=lambda x:
                (
                    board.reset(),
                    popup.dismiss()
                )
            )


            popup.open()



        board.on_win_callback=show_result





        # ======================
        # 底部按钮
        # ======================

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


        level=flat_button(
            "难度：中",
            (
                0.4,
                0.4,
                0.5,
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



        # 难度切换

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


            if index>=len(levels):

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
