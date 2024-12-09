import time
from tkinter import *

from numpy import clip

EMPTY_SYMBOL = '_'
SPEED = 1
REC_SIZE = 120
WIDTH = 1500
HEIGHT = 300

class Direction:
    LEFT = -1
    RIGHT = 1

    def from_string(s: str):
        if s == 'L':
            return Direction.LEFT
        elif s == 'R':
            return Direction.RIGHT
        elif s == '▷':
            return Direction.RIGHT
        elif s == '◁':
            return Direction.LEFT
        else:
            raise Exception(f'Invalid direction: {s}')
        
    def __str__(self):
        if self == Direction.LEFT:
            return '◁'
        elif self == Direction.RIGHT:
            return '▷'
        else:
            raise Exception(f'Invalid direction: {self}')

class Tape:
    def __init__(self, initial_word: str):
        self.tape = [c for c in initial_word]
        if len(self.tape) == 0:
            self.tape = [EMPTY_SYMBOL]
        self.index = 0

    def move(self, direction: Direction):
        if direction == Direction.LEFT:
            self.index -= 1
            if self.index < 0:
                self.tape.insert(0, EMPTY_SYMBOL)
                self.index = 0
        elif direction == Direction.RIGHT:
            self.index += 1
            if self.index >= len(self.tape):
                self.tape.append(EMPTY_SYMBOL)
        
    def read(self):
        return self.tape[self.index]
    
    def write(self, value):
        self.tape[self.index] = value

    def write_move(self, value, direction: Direction):
        self.write(value)
        self.move(direction)

    def string_state(self, state: 'State'):
        # insert state in red at index and return string
        return "".join(self.tape[:self.index]) + "\033[31m" + state.name + "\033[0m" + "".join(self.tape[self.index:])
    
    def draw(self, canvas: Canvas, offset: float = 0):
        # calculate how many squares to draw
        n_rects = WIDTH // REC_SIZE +2

        # calculate index so that the tape is centered
        index_offset = n_rects // 2 - self.index

        # draw tape
        for i in range(-1,int(n_rects)):
            t_ind = int(i - index_offset)

            tx = i * REC_SIZE + offset
            ty = HEIGHT/2 + REC_SIZE / 2
            tx2 = (i+1) * REC_SIZE + offset
            ty2 = HEIGHT/2 - REC_SIZE / 2

            canvas.create_rectangle(tx, ty, tx2, ty2, fill="white")
            
            tx = (i+1/2) * REC_SIZE + offset
            ty = HEIGHT/2 
            if 0 <= t_ind < len(self.tape):
                canvas.create_text(tx, ty, text=self.tape[t_ind], anchor=CENTER , font=("Arial", 16, "bold"))
            else:
                canvas.create_text(tx, ty, text=EMPTY_SYMBOL, anchor=CENTER)

        # draw hollow square in center color red 
        tx = (n_rects/2) * REC_SIZE - 5
        ty = HEIGHT/2 + REC_SIZE / 2 + 10
        tx2 = tx + REC_SIZE + 10
        ty2 = ty - REC_SIZE - 20
        canvas.create_rectangle(tx, ty, tx2, ty2, outline="red", width=5)
        
class State:
    def __init__(self, name: str , transitions: list['Transition'] = []):
        self.name = name
        self.transitions = transitions

    def parse(self,line: str, state_dict: dict['State']):
        line = line.strip()
        line = line.strip(",")
        line = line[1:-1]
        line = line.strip(" ")
        
        transitions = []
        while len(line) > 0:
            # read everything up to :
            t_index = line.find(":")
            name = line[:t_index]
            name = name.strip()
            n_index = name.find(" ")
            name = name[n_index+1:]
            n_index = name.find(",")
            name = name[n_index+1:]
            line = line[t_index+1:]

            # read everything up to )
            c_index = line.find(")")
            transition_text = line[:c_index+1]
            line = line[c_index+1:]

            # remove ( and )
            transition_text = transition_text.strip(" ")
            transition_text = transition_text.strip("(")
            transition_text = transition_text.strip(")")

            # split by ,
            transition_text_entries = transition_text.split(",")
            for transition_text_line in transition_text_entries:
                if name not in state_dict:
                    raise Exception(f"State {name} not found")
                if transition_text_line.strip('"').strip() == "":
                    continue
                transition = Transition.parse(self, state_dict[name], transition_text_line)
                transitions.append(transition)
            
        self.transitions = transitions
        
    def __repr__(self):
        return f"State[{self.name}:{"".join([str(t) for t in self.transitions])}]"
    
    def __str__(self):
        return f"State[{self.name}:{"".join([str(t) for t in self.transitions])}]"

class Transition:
    def __init__(self, cur_state: State, new_state: State, cur_value: str, new_value: str, direction: Direction):
        self.cur_state = cur_state
        self.new_state = new_state
        self.cur_value = cur_value
        self.new_value = new_value
        self.direction = direction

    def parse(cur_state: State, new_state: State, line: str) -> 'Transition':
        # remove ""
        line = line.strip('"')
        line = line.strip(' ')
        cur_value, _, new_value, direction = line
        return Transition(cur_state, new_state, cur_value, new_value, Direction.from_string(direction))
    
    def __repr__(self):
        return f"Transition[{self.cur_state.name}->{self.new_state.name},{self.cur_value}/{self.new_value}{self.direction}]"
    
    def __str__(self):
        return f"Transition[{self.cur_state.name}->{self.new_state.name},{self.cur_value}/{self.new_value}{self.direction}]"

class TuringMachine:
    def __init__(self, states: list[State]):
        self.tape = Tape('')
        self.states = states
        self.cur_state = states[0]

    def run(self, initial_word: str):
        self.reset(initial_word)
        i = 0
        while True:
            i += 1
            self.step()
            if self.cur_state is None:
                break
        return i, self.tape

    def run_history(self, initial_word: str):
        self.reset(initial_word)
        history = []
        while True:
            history.append(self.tape.string_state(self.cur_state))
            self.step()
            if self.cur_state is None:
                break
        return history

    def run_animated(self, initial_word: str):
        root = Tk()
        root.title("Turing Machine")

        canvas = Canvas(root, width=WIDTH, height=HEIGHT, bg="#131916")
        canvas.pack()

        self.reset(initial_word)
        
        def animation(i, dir):
            k = i % ( 61 // SPEED )
            if k == 0:
                t = self.step()
                if self.cur_state is None:
                    # draw text "HALTED"
                    tx = WIDTH / 2
                    ty = HEIGHT / 2
                    canvas.create_text(tx, ty, text="HALTED", fill="RED", font=("Arial", 20))
                    root.update()
                    return 
                dir = t.direction * -1
            def easing(x):
                x = x / ( 61 // SPEED )
                y = 3 * x**2 - 1.9 * x**3 - 0.1
                return clip(y,0,1)
            offset =   REC_SIZE * easing(k) * dir  - REC_SIZE * dir 
            canvas.delete("all")
            self.tape.draw(canvas, offset)
            # draw cur state name
            tx = WIDTH / 2 + REC_SIZE * 4 / 3
            ty = HEIGHT / 2 - REC_SIZE / 2 -30
            canvas.create_text(tx, ty, text=self.cur_state.name, fill="white", font=("Arial", 20))
            root.update()
            
            root.after(int(1/120 * 1000), animation, i+1 , dir)


        animation(0,0)
        # wait for user to close window
        root.mainloop()
        

    def step(self):
        cur_value = self.tape.read()
        for transition in self.cur_state.transitions:
            if transition.cur_value == cur_value:
                self.tape.write_move(transition.new_value, transition.direction)
                self.cur_state = transition.new_state
                return transition
        else:
            self.cur_state = None
            
    def reset(self, initial_word: str):
        self.tape = Tape(initial_word)
        self.cur_state = self.states[0]

    def parse(text: str) -> 'TuringMachine':
        # construct states_dict
        states_dict = {}

        for line in text.split("\n"):
            n_index = line.find(":")
            name = line[:n_index]
            states_dict[name] = State(name)

        for line in text.split("\n"):
            n_index = line.find(":")
            name = line[:n_index]
            t = line[n_index+1:]
            State.parse(states_dict[name], t, states_dict)

        return TuringMachine(list(s for s in states_dict.values() if s.name != ''))

    def __repr__(self):
        return f"TuringMachine[Tape:{self.tape.tape}\nStates: {self.states}\nCurrent State: {self.cur_state}]"
    
    def __str__(self):
        return f"Tape: {self.tape.tape} States: {self.states} Current State: {self.cur_state}"

def main():
    
    example1 = """
q0: ( q0:("a/A▷","b/b▷"), q1:("▢/▢◁") ), 
q1: (q1:("a/a◁","A/A◁","b/b◁") , q2: ("▢/#▷")),
q2: (q2: ("a/a▷","b/b▷","1/1▷","#/#▷"), q3: ("A/a◁")),
q3: (q3: ("a/a◁","#/#◁","b/b◁","1/1◁"), q2: ("▢/1▷"))
""".replace("▢",EMPTY_SYMBOL)

    tm = TuringMachine.parse(example1)

    def run(word: str):
        h = tm.run_history(word)
        print(f"History for '{word}' of length {len(h)}:")
        for i in h:
            print(i)
        print()

    run("")
    run("a")
    run("b")
    run("aabbaba")

    example2 = """
q0: ( q0:("a/A▷","b/b▷"), q1:("▢/▢◁") ), 
q1: (q1:("a/a◁","A/A◁","b/b◁") , q4: ("▢/#◁")),
q2: (q2: ("a/a▷","b/b▷","1/1▷","0/0▷","#/#▷"), q3: (" A/a◁")),
q3: (q3: ("a/a◁","#/#◁","b/b◁","1/0◁"), q2: ("▢/1▷","0/1▷"," ")),
q4: (q2: ("▢/0▷"))""".replace("▢",EMPTY_SYMBOL)

    tm = TuringMachine.parse(example2)

    run("")
    run("a")
    run("b")
    run("aabbaba")
    run("aaaaaa")

    example3 = """
q0: ( q1:("a/a▷"), q2:("b/b▷"), q6: ("▢/▢◁") ),
q1: ( q3:("b/b◁"), q1: ("a/a▷"), q6:("▢/▢◁")),
q2: ( q4: ("a/a◁"), q2:("b/b▷"), q6:("▢/▢◁")),
q3: (q0: ("a/A▷")),
q4: (q0: ("b/B▷") ),
q6: ( q6: ("a/a◁","A/A◁","b/b◁","B/B◁") , q7:("▢/#◁")),
q7: (q8:("▢/0▷")),
q8: (q8:("a/a▷","b/b▷","1/1▷","0/0▷","#/#▷"),q9:("A/a◁","B/b◁"," ")),
q9: (q9: ("a/a◁","#/#◁","b/b◁","1/0◁") , q8: ("▢/1▷","0/1▷"," ") ),""".replace("▢",EMPTY_SYMBOL)

    tm = TuringMachine.parse(example3)

    run("")
    run("ba")
    run("ab")
    run("aabbababbba")
    run("bababababa")

    t1 = time.time()
    i, t = tm.run("ba"*3)
    print(i , time.time() - t1 , t.tape)

    tm.run_animated("baab"*1)

if __name__ == '__main__':
    main()
