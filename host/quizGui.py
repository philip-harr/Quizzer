from pdb import main
import string
from time import sleep
import tkinter as tk
from tkinter import Place
from turtle import color
from click import prompt
from more_itertools import last
import serial
import os
import threading

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
                self.ser = serial.Serial("/dev/ttyUSB0", 500000, timeout=1)
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
        self.ser.close()

def setPin(mc, name):
    global teamList, buttonThread, abortButtonThread
    while True:
        mc.clearPin()
        pin = int.from_bytes(mc.getPinOnce(), 'big')
        if pin != 123:            
            success=True
            for team in teamList:
                if team.pinNumber == pin:
                    print("Pin already used!\n")
                    print("Try again!\n")
                    success = False
                    break
            if success:
                break
        else:
            sleep(0.2)

        if abortButtonThread:
            return

    for item in teamList:
        if name == item.name:
            item.pinNumber = pin
            
    printLabels()

teamList = []
buttonThread = None
abortButtonThread = False
def addteam(window, mc):
    global buttonThread
    name = tk.simpledialog.askstring(title="Team",
                                  prompt="What's your Team Name?:")
    if name != None:
        if len(name) >= 20:
            name = name[0:19] + "."
        
        teamList.append(Team(name, -100))
        printLabels()
        window.update()
        buttonThread = threading.Thread(target=setPin, args=(mc, name))
        buttonThread.start()

# def resetPin(mc):
#     number = tk.simpledialog.askinteger(title="Reset Pin!",
#                                      prompt="Teamnumber?")

#     if number > 0 and number <= len(teamList):
#         print("Press new button")
#         teamList[number-1].pinNumber = -100
#         printLabels()
#         setPin(mc, number-1)
    
#     printLabels()

teamLabels = []
def printLabels():
    global teamList, teamLabels

    for teamLabel in teamLabels:
        teamLabel.destroy()

    i = 0
    for team in teamList:
      if team.pinNumber == -100:
        text = team.name + ": Set Btn"
      else:
        text = team.name + ": " +  str(team.points)

      label = tk.Label(window, text=text, font=("Roboto", 18))
      label.place(x=15, y=(i*40)+60)
      teamLabels.append(label)
      i += 1

def removeTeam():
    global teamlabels, teamList, abortButtonThread
    number = tk.simpledialog.askinteger(title="Remove Team",
                                     prompt="Put in number of team to remove")
    if number != None:
        if number > 0 and number <= len(teamList):
            if teamList[number-1].pinNumber == -100 and buttonThread != None:
                abortButtonThread = True
                buttonThread.join()
                abortButtonThread = False
                buttonThread = None

            del teamList[number-1]
            printLabels()
   
def clearAll():
    global teamList, buttonThread, abortButtonThread 
    res = tk.messagebox.askyesno(title="Clear Everything", message="Are you sure?")
    if res == True:
        teamList = []
        if buttonThread != None:
            abortButtonThread = True
            buttonThread.join()
            abortButtonThread = False
            buttonThread = None

        printLabels()

lastTeamAnswered = None
def adjustPoints(adjbtn):
    global lastTeamAnswered

    if lastTeamAnswered == None:
        team = tk.simpledialog.askinteger(title="Adjust Points",
                                        prompt="Put in number of team to adjust points")
    else:
        i = 1
        for item in teamList:
            if item.name == lastTeamAnswered.name:
                team = i
                break
            i += 1
        lastTeamAnswered = None
    
    if team != None:
        if team > 0 and team <= len(teamList):
            teamName = teamList[team-1].name
            points = tk.simpledialog.askinteger(title="Adjust Points",
                                            prompt= "Add/Subtract points for team: " + teamName)
            teamList[team-1].points += points
        else:
            print("Team number not available")

    adjbtn.configure(bg="lightgreen")
    printLabels()

abort = False
def question(mc,window, btn_game, btn_adj):
    global abort, lastTeamAnswered, questionThread
    mc.clearPin()  
    
    while True:
        pin = int.from_bytes(mc.getPinOnce(), 'big')
        if pin != b'{':
            to_answer = None
            for team in teamList:
                if team.pinNumber == pin:
                    to_answer = team 
                    lastTeamAnswered = team
                    break

            if to_answer != None:
                msg = "Team " + to_answer.name + " to answer the question!"
                answer = tk.messagebox.showinfo(title="Answer", message=msg)
                btn_game.configure(bg="lightgreen", text="Game On!")
                btn_adj.configure(bg="yellow")
                printLabels()
                break
                            
                # if answer == "yes":
                #     points = tk.simpledialog.askinteger(title="Congrats!",
                #                                 prompt="Number of pts:",
                #                                 parent=window)
                #     to_answer.points += points
                #     break
                # else:
                #     points = tk.simpledialog.askinteger(title="Thats too bad!",
                #                                 prompt="Number of pts to subtract:",
                #                                 parent=window)
                #     to_answer.points -= points
                #     break
        else:
            sleep(0.1)

        if abort:
            abort = False
            break

    mc.clearPin()
    questionThread = None


questionThread = None
def handleQuestion(mc, btn, adjbtn, window):
    global questionThread, abort, teamList
    if len(teamList) == 0:
        print("Not possible when no Teams")
        return

    if questionThread == None:
        btn.configure(text="Abort...", bg="yellow")
        questionThread = threading.Thread(target=question, args=(mc, window, btn, adjbtn))
        questionThread.start()

    else:
        abort = True
        questionThread.join()
        questionThread = None
        btn.configure(bg="lightgreen", text="Game On!")
        abort = False


    printLabels()


if __name__ == "__main__":

    mc = SerialHandler()


    window = tk.Tk()
    window.geometry("700x310")
    window.title("Digitaltechnik Jeopardy")

    # window.

    # for i in range(0, 5):
    (tk.Label(window, text="Teams:", font=("Roboto", 25))).place(x=15, y=15)
        

    clearBtn = tk.Button(window, text="Clear All", font=("Roboto", 18), command= lambda: clearAll())
    clearBtn.place(x=530, y=10, height=50, width=160)
    
    removeTeamBtn = tk.Button(window, text="Rem. Team", command= lambda: removeTeam(), font=("Roboto", 18))
    removeTeamBtn.place(x=530, y=70, height=50, width=160)

    addTeamBtn = tk.Button(window, text="Add Team", command= lambda: addteam(window, mc), font=("Roboto", 18))
    addTeamBtn.place(x=530, y=130, height=50, width=160)

    # setTeamBtn = tk.Button(window, text="Reset Btn", command= lambda: resetPin(mc), font=("Roboto", 18))
    # setTeamBtn.place(x=530, y=190, height=50, width=160)

    adjBtn = tk.Button(window, bg="lightgreen", text="Adj Pts", font=("Roboto", 18), command= lambda: adjustPoints(adjBtn))
    adjBtn.place(x=530, y=190, height=50, width=160)
    
    gameOn = tk.Button(window, text="Game On!", command= lambda: handleQuestion(mc, gameOn, adjBtn, window), font=("Roboto", 18), bg="lightgreen")
    gameOn.place(x=530, y=250, height=50, width=160)

    window.mainloop()
    mc.cleanup()