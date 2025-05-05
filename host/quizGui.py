from pdb import main
import string
from time import sleep
import mttkinter as mtk
tk = mtk.mtTkinter

import tkinter as tk_orig
from tkinter import filedialog
from tkinter.font import Font
from tkinter import simpledialog
from tkinter import messagebox
from turtle import color
from click import prompt
import serial
import os
import threading
import configparser
import platform
import subprocess

mc = []
teamList = []
teamLabels = []
abortMC = False
abortAddTeam = False
questionThread = None
questionList = []
activeTeam = None


class Team:
    def __init__(self, name, pin) -> None:
        self.name = name
        self.points = 0
        self.pinNumber = pin

    def incPoints(self, increment) -> None:
        self.points += increment

class SerialHandler:
    def __init__(self) -> None:
        device = "/dev/ttyUSB0"
        while True:
            if os.path.exists(device):
                self.ser = serial.Serial(device, 500000, timeout=1)
                self.ser.read_all()
                break
            else:
                print("Quizzer not connected!")
                print("Connect and press Enter to try again!")
                input()
        
    def getPinOnce(self):
        self.ser.write(b'GP\n')
        while self.ser.in_waiting == 0:
            sleep(0.01)

        pin = self.ser.read()
        return pin
                 

    def getPin(self) -> int:
        
        while True:
            pin = self.getPinOnce()
            if pin != b'{':
                self.clearPin()                
                break

            sleep(0.2)
    
        return pin

    def clearPin(self) -> None:
        while True:
            self.ser.write(b'CP\n')
            sleep(0.1)
            self.ser.write(b'GP\n')
            if self.ser.in_waiting > 0:
                pin = self.ser.read()
                if pin == b'{':
                    break


    def cleanup(self):
        try:
            self.ser.close()
        except Exception:
            pass

class ActiveQuestion:
    def __init__(self, btn, points, text):
        self.btn = btn
        self.points = points
        self.text = text
        self.active = True

    def deactivate(self):
        self.active = False
    def activate(self):
        self.active = True

    @classmethod
    def default(cls):
        # Create an instance with default values
        a = cls(0, 0, "")
        a.deactivate()
        return a

activeQuestion = ActiveQuestion.default()


def checkPin(pinNumber):
    global teamList
    if pinNumber == 123: #magic value for no pin was pressed
        return False

    for team in teamList:
        if team.pinNumber == pinNumber:
            tk_orig.messagebox.showinfo("", "Pin already used! Try again!")
            return False

    return True



def setPin(mc, team, dialog):
    global abortAddTeam, window

    while True:
        mc.clearPin()
        pin = int.from_bytes(mc.getPinOnce(), 'big')
        if checkPin(pin):
            team.pinNumber = pin
            window.after(0, lambda: endAddTeamFunc(team, dialog, "done"))
            break
        else:
            sleep(0.1)

        if abortAddTeam:
            break


def endAddTeamFunc(team, dialog, reason, thread = None):
    global abortAddTeam, teamList

    if reason == "done":
        pass
    if reason == "abort":
        abortAddTeam = True
        teamList.remove(team)
        thread.join()

    printLabels()
    dialog.destroy()


def addteam(window, mc):
    global questionThread, abortAddTeam

    if questionThread is not None:
        tk_orig.messagebox.showinfo("","Not possible when there is an active question!")
        return

    name = tk_orig.simpledialog.askstring(title="Team", prompt="What's your Team Name?:")

    if name != None:
        if len(name) >= 30:
            name = name[0:29] + "."

        team = Team(name, -100)
        teamList.append(team)
        printLabels()

        dialog = tk.Toplevel(window)
        dialog.title("Add Team")
        dialog.geometry("200x100")
        dialog.grab_set()

        abortAddTeam = False
        thread = threading.Thread(target=setPin, args=(mc, team, dialog))
        thread.start()

        # "Press Button" label
        press_button_label = tk.Label(dialog, text="Press Button")
        press_button_label.pack(pady=10)
        # Cancel button
        cancel_button = tk.Button(dialog, text="Cancel")
        cancel_button.configure(command=lambda btn=cancel_button: endAddTeamFunc(team, dialog, "abort", thread))
        cancel_button.pack(pady=10)

        window.update()


def printLabels():
    global teamList, teamLabels, y_questions

    for teamLabel in teamLabels:
        teamLabel.destroy()

    i = 0
    for team in teamList:
      if team.pinNumber == -100:
        text = team.name + ": Set Btn"
      else:
        text = team.name + ": " + str(team.points)

      label = tk.Label(window, text=text, font=("Roboto", 18))
      label.place(x=15, y=y_questions+(i*40)+60)
      teamLabels.append(label)
      i += 1

def removeTeam():
    global teamList
    number = tk_orig.simpledialog.askinteger(title="Remove Team",
                                     prompt="Put in number of team to remove")
    if number != None:
        if number > 0 and number <= len(teamList):
            del teamList[number-1]
            printLabels()
   
def clearAll():
    global teamList
    res = tk_orig.messagebox.askyesno(title="Clear Everything", message="Are you sure?")
    if res:
        teamList = []
        printLabels()

def adjustPoints():
    global teamList, window
    def changePoints():
        team = team_number_entry.get()
        points = points_entry.get()
        popup.destroy()
        try:
            if team is not None and points is not None:
                if 0 < int(team) <= len(teamList):
                    team = teamList[int(team)-1]
                    team.incPoints(int(points))
                else:
                    print("Team number not available")
        except Exception:
            pass

        printLabels()

    popup = tk.Toplevel(window)
    popup.title("Adjust Points")

    team_number_label = tk.Label(popup, text="Team Number:")
    team_number_label.pack(pady=10)

    team_number_entry = tk.Entry(popup)
    team_number_entry.pack(pady=5)

    points_label = tk.Label(popup, text="Points:")
    points_label.pack(pady=10)

    points_entry = tk.Entry(popup)
    points_entry.pack(pady=5)

    okay_button = tk.Button(popup, text="OK", command=changePoints)
    okay_button.pack(pady=10)

    popup.grab_set()  # Block main window input
    popup.wait_window()


def calculateAnswer(team, activeQuestion, correct, cont, popup):
    if correct:
        team.incPoints(int(activeQuestion.points))
    else:    
        team.incPoints(-int(activeQuestion.points))

    printLabels()
    popup.destroy()
    on_question_event("popupClose", continueQuestion=cont)


def show_popup(team, activeQuestion):

    popup = tk.Toplevel()
    popup.title("Answer:")
    popup.geometry("630x110")

    label = tk.Label(popup, text="{}{}{}".format('Team: "', team.name, '"'), font=Font(size=16))
    label.place(x=10, y=10)

    correct_button = tk.Button(popup, text="Correct", command=lambda: calculateAnswer(team, activeQuestion, True, False, popup))
    correct_button.place(x=10, y=50, height=50, width=200)
    
    wrong_continue_button = tk.Button(popup, text="Wrong & Continue", command=lambda: calculateAnswer(team, activeQuestion, False, True, popup))
    wrong_continue_button.place(x=215, y=50, height=50, width=200)
    
    wrong_close_button = tk.Button(popup, text="Wrong & Close", command=lambda: calculateAnswer(team, activeQuestion, False, False, popup))
    wrong_close_button.place(x=420, y=50, height=50, width=200)


def findTeam():
    global mc
    pin = int.from_bytes(mc.getPinOnce(), 'big')

    if pin == b'{':
        return None
    
    for team in teamList:
        if team.pinNumber == pin:
            return team
    
    return None

def mcAction():
    global mc, abortMC, window, activeTeam
    
    mc.clearPin()  
    while True:
        if abortMC:
            break

        team = findTeam()
        if team != None:
            mc.clearPin()
            activeTeam = team
            window.after(0, buttonPress)
            break
        else:
            sleep(0.01)

def buttonPress():
    on_question_event("buttonPress")



def parse_question(question):
    if question.startswith("**IMAGE**"):
        return True, question[9:]
    else:
        return False, question

def open_image_with_viewer(image_path):
    system = platform.system()

    if system == 'Linux':
        try:
            subprocess.run(['xdg-open', image_path])
        except FileNotFoundError:
            print("Could not open the image. Make sure the 'xdg-open' command is available.")
    elif system == 'Windows':
        try:
            subprocess.run(['start', '', image_path], shell=True)
        except FileNotFoundError:
            print("Could not open the image. Make sure the 'start' command is available.")
    else:
        print("Unsupported operating system.")



displayQuestionHeight = 180
def displayQuestion(question):
    global window, y_questions, x_questions

    image, local_question = parse_question(question)

    frame = tk.Frame(window, borderwidth=2, relief="solid")
    frame.place(x=10, y=y_questions-190, height=displayQuestionHeight, width=x_questions-20)

    q1 = tk.Label(window, text="Answer:", font=("Roboto", 16))
    q1.place(x=30, y=y_questions-180)

    if image:
        q2 = tk.Label(window, text=formatText("**Image**", 75), font=("Roboto", 14), justify="left", anchor="e")
        open_image_with_viewer(local_question)
    else:
        q2 = tk.Label(window, text=formatText(local_question, 75), font=("Roboto", 14), justify="left", anchor="e")

    q2.place(x=30, y=y_questions-130)

def handleQuestion(text, points, btn):
    global activeQuestion, questionThread

    if len(teamList) == 0:
        tk_orig.messagebox.showinfo("", "Not possible when no teams are registered.")
        return

    if questionThread is not None:
        if activeQuestion.active:
            activeQuestion.btn.configure(bg="green")

        activeQuestion = ActiveQuestion(btn, points, text)
        on_reset()

    else:
        activeQuestion = ActiveQuestion(btn, points, text)
        startQuestion()

def startQuestion():
    global activeQuestion, questionThread

    activeQuestion.btn.configure(bg="yellow")
    abortBtn.config(state="normal")
    displayQuestion(activeQuestion.text)
    questionThread = threading.Thread(target=mcAction)
    questionThread.start()


def read_config_file(file_path):
    config = configparser.ConfigParser()

    try:
        config.read(file_path)
        config_dict = {}
        for section in config.sections():
            section_dict = []
            for key, value in config.items(section):
                section_dict.append((key, value))
            config_dict[section] = section_dict

        return config_dict
    except Exception:
        return None

def formatText(text, position):
    if len(text) > position:

        last_whitespace = text[:position].rfind(" ")
        if last_whitespace == -1:
            last_whitespace = position

        text = text[:last_whitespace+1] + '\n' + text[last_whitespace+1:]

    return text

class TilePlacer:

    def __init__(self):
        self.x_max = 0
        self.y_max = 0
        self.question_list = []

    def load_questions(self):
        while True:
            name = tk_orig.filedialog.askopenfilenames()
            q_list = read_config_file(name)
            if q_list is not None:
                break

        self.question_list = q_list

    def print_tiles(self, window):
        global tk

        y_corr = 10
        x_corr = 10
        y_max = 10

        for sec, qList in self.question_list.items():
            button = tk.Button(window, text=formatText(sec, 15), font=Font(weight="bold"))
            button.place(x=x_corr, y=y_corr, width=200, height=50)

            i = 1
            for points, entry in qList:
                button = tk.Button(window, bg="green", text=str(points))
                button.configure(command=lambda e=entry, p=points, btn=button: handleQuestion(e, p, btn))

                y = y_corr + i * 50
                button.place(x=x_corr, y=y, width=200, height=50)
                if y > y_max:
                    y_max = y

                i += 1

            x_corr += 200

        self.y_max = y_max + 50
        self.x_max = x_corr + 10

    def do_it(self, window):
        self.load_questions()

        if self.question_list is not None:
            self.print_tiles(window)

    def getx(self):
        return self.x_max

    def gety(self):
        return self.y_max


def abortQuestionThread():
    global abortMC, questionThread, abortBtn
    abortMC = True
    questionThread.join()
    questionThread = None
    abortMC = False
    abortBtn.configure(state="disabled")

def on_question_event(event, continueQuestion = False):
    global activeQuestion, activeTeam

    if event == "abort":
        abortQuestionThread()
        activeQuestion.btn.configure(bg="grey", state="disabled")
        activeQuestion.deactivate()

    if event == "buttonPress":
        team = activeTeam
        if team != None and activeQuestion.active:
            show_popup(team, activeQuestion)

    if event == "reset":
        abortQuestionThread()
        handleQuestion(activeQuestion.text, activeQuestion.points, activeQuestion.btn)

    if event == "popupClose":
        if continueQuestion:
            startQuestion()
        else:
            activeQuestion.btn.configure(bg="grey", state="disabled")
            abortQuestionThread()


def on_reset():
    on_question_event("reset")

def abort_btn_func():
    on_question_event("abort")

if __name__ == "__main__":
    mc = SerialHandler()

    window = tk.Tk()
    window.title("Digitaltechnik Jeopardy")

    questionTiles = TilePlacer()
    questionTiles.do_it(window)
    y_questions = questionTiles.gety() + displayQuestionHeight + 20
    x_questions = questionTiles.getx()

    window.geometry("{}{}{}".format(str(x_questions), "x", str(y_questions+310)))
    (tk.Label(window, text="Teams:", font=("Roboto", 25))).place(x=20, y=y_questions+10)


    btnwidth = 200
    btnxcorr = x_questions - btnwidth - 10
    clearBtn = tk.Button(window, text="Clear All", font=("Roboto", 18), command= lambda: clearAll())
    clearBtn.place(x=btnxcorr, y=y_questions+10, height=50, width=btnwidth)

    removeTeamBtn = tk.Button(window, text="Rem. Team", command= lambda: removeTeam(), font=("Roboto", 18))
    removeTeamBtn.place(x=btnxcorr, y=y_questions+70, height=50, width=btnwidth)

    addTeamBtn = tk.Button(window, text="Add Team", command= lambda: addteam(window, mc), font=("Roboto", 18))
    addTeamBtn.place(x=btnxcorr, y=y_questions+130, height=50, width=btnwidth)

    # setTeamBtn = tk.Button(window, text="Reset Btn", command= lambda: resetPin(mc), font=("Roboto", 18))
    # setTeamBtn.place(x=btnxcorr, y=190, height=50, width=200)

    adjBtn = tk.Button(window, text="Adj Pts", font=("Roboto", 18), command= lambda: adjustPoints())
    adjBtn.place(x=btnxcorr, y=y_questions+190, height=50, width=btnwidth)

    abortBtn = tk.Button(window, text="Abort!", command= lambda: abort_btn_func(), font=("Roboto", 18), state="disabled")
    abortBtn.place(x=btnxcorr, y=y_questions+250, height=50, width=btnwidth)

    window.mainloop()
    mc.cleanup()