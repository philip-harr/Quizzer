from pdb import main
import string
from time import sleep
import tkinter as tk
from tkinter import Place, simpledialog
from turtle import color
import serial
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
        self.ser = serial.Serial("/dev/ttyUSB0", 500000, timeout=1)
        self.ser.read_all()
        
    
    def getPin(self) -> int:
        
        while True:
            self.ser.write(b'GP\n')
            if self.ser.in_waiting > 0:
                pin = self.ser.read()
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

teamList = []
def addteam(window, mc):
    name = simpledialog.askstring(title="Team",
                                  prompt="What's your Team Name?:")
    if name != None:
        if len(name) >= 20:
            name = name[0:19] + "."
        
        teamList.append(Team(name, -100))
        printLabels()
        window.update()
        setPin(mc, -1)

def setPin(mc, index):
    global teamList
    mc.clearPin()
    while True:
        pin = int.from_bytes(mc.getPin(), 'big')
        success=True
        for team in teamList:
            if team.pinNumber == pin:
                print("Pin already used!\n")
                print("Try again!\n")
                success = False
                break
        if success:
            break

    teamList[index].pinNumber = pin
    printLabels()

def resetPin(mc):
    number = simpledialog.askinteger(title="Reset Pin!",
                                     prompt="Teamnumber?")

    if number > 0 and number <= len(teamList):
        setPin(mc, number-1)
    
    printLabels()

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

      label = tk.Label(window, text=text, font=("Roboto", 20))
      label.place(x=15, y=(i*40)+60)
      teamLabels.append(label)
      i += 1

def removeTeam():
    global teamlabels, teamList
    number = simpledialog.askinteger(title="Remove Team",
                                     prompt="Put in number of team to remove")
    if number > 0 and number <= len(teamList):
        del teamList[number-1]
        printLabels()
   
def clearAll():
    teamList = []
    printLabels()

def adjustPoints():
    team = simpledialog.askinteger(title="Adjust Points",
                                    prompt="Put in number of team to adjust points")
    
    if team > 0 and team <= len(teamList):
        points = simpledialog.askinteger(title="Adjust Points",
                                        prompt="Put in new number of points")
        teamList[team-1].points = points
    else:
        print("Team number not available")

    printLabels()

def question(mc, btn, window):
    mc.clearPin()
    # btn.configure(bg="yellow", text="Waiting...")
    btn.configure(text="Waiting...", bg="yellow")
    window.update()
    # window.update()
    
    while True:
        pin = int.from_bytes(mc.getPin(), 'big')

        to_answer = None
        for team in teamList:
            if team.pinNumber == pin:
                to_answer = team 
                break

        if to_answer != None:
            msg = to_answer.name + ": What is the answer?"
            
            answer = tk.messagebox.askquestion(title="Answer", message=msg)
            
            if answer == "yes":
                points = simpledialog.askinteger(title="Congrats!",
                                            prompt="Number of pts:")
                to_answer.points += points
                break
        else:
            mc.clearPin()
            break

        mc.clearPin()
    printLabels()
    btn.configure(bg="lightgreen", text="Game On!")

if __name__ == "__main__":

    mc = SerialHandler()


    window = tk.Tk()
    window.geometry("700x300")
    window.title("Digitaltechnik Quiz")

    # window.

    # for i in range(0, 5):
    (tk.Label(window, text="Teams:", font=("Roboto", 25))).place(x=15, y=15)
        

    clearBtn = tk.Button(window, text="Clear All", font=("Roboto", 20), command= lambda: clearAll())
    clearBtn.place(x=550, y=00, height=50, width=150)
    
    removeTeamBtn = tk.Button(window, text="Rem. Team", command= lambda: removeTeam(), font=("Roboto", 20))
    removeTeamBtn.place(x=550, y=50, height=50, width=150)

    addTeamBtn = tk.Button(window, text="Add Team", command= lambda: addteam(window, mc), font=("Roboto", 20))
    addTeamBtn.place(x=550, y=100, height=50, width=150)

    setTeamBtn = tk.Button(window, text="Reset Btn", command= lambda: resetPin(mc), font=("Roboto", 20))
    setTeamBtn.place(x=550, y=150, height=50, width=150)

    adjBtn = tk.Button(window, text="Adj Pts", font=("Roboto", 20), command= lambda: adjustPoints())
    adjBtn.place(x=550, y=200, height=50, width=150)
    
    gameOn = tk.Button(window, text="Game On!", command= lambda: question(mc, gameOn, window), font=("Roboto", 20), bg="lightgreen")
    gameOn.place(x=550, y=250, height=50, width=150)

    window.mainloop()
    mc.cleanup()