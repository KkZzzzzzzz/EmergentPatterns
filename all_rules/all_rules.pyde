mode = 'all'
show_info = True
running = True


view_radius = 60.0
max_speed = 3.0
max_force = 0.06
show_radius = True
weight_sep = 1.5
weight_ali = 1.0
weight_coh = 1.0

flock = []

"""
This is the start of my custom class
"""
class Boid(object):
    def __init__(self, x, y):
        self.pos = PVector(x, y)
        self.vel = PVector.fromAngle(random(TWO_PI))
        self.vel.mult(random(1.0, max_speed))
        self.acc = PVector(0, 0)
    
    
    def update(self):
        self.vel.add(self.acc)
        if self.vel.mag() > max_speed:
            self.vel.setMag(max_speed)
        self.pos.add(self.vel)
        self.acc.mult(0)
    
    def apply_force(self, f):
        self.acc.add(f)
        
    def steer_to(self, target):
        desired = PVector.sub(target, self.pos)
        desired.setMag(max_speed)
        steer = PVector.sub(desired, self.vel)
        if steer.mag() > max_force: steer.setMag(max_force)
        return steer
    
    def rule_separation(self, others):
        steer = PVector(0, 0)
        count = 0
        for o in others:
            if o is self: continue
            d = self.pos.dist(o.pos)
            if d == 0 or d >= view_radius: continue
            diff = PVector.sub(self.pos, o.pos)
            diff.normalize()
            diff.div(d)
            steer.add(diff)
            count += 1
        if count > 0:
            steer.div(count)
            steer.setMag(max_speed)
            steer.sub(self.vel)
            if steer.mag() > max_force: steer.setMag(max_force)
        return steer
    
    def rule_alignment(self, others):
        # need to find aver. vel. of neighbors
        avg_vel = PVector(0, 0) 
        count = 0
        for o in others:
            if o is self: continue
            if self.pos.dist(o.pos) < view_radius:
                avg_vel.add(o.vel)
                count += 1
        if count > 0:
            avg_vel.div(count)
            avg_vel.setMag(max_speed)
            steer = PVector.sub(avg_vel, self.vel)
            if steer.mag() > max_force:
                steer.setMag(max_force)
            return steer
        return PVector(0, 0) # when count==0
    
    def apply_rules(self, others):
        sep = self.rule_separation(others)
        ali = self.rule_alignment(others)
        coh = self.rule_cohesion(others)
        steer = PVector(0,0)
        if mode == 'sep':
            sep.mult(weight_sep)
            steer.add(sep)
        elif mode == 'ali':
            ali.mult(weight_ali)
            steer.add(ali)
        elif mode == 'coh':
            coh.mult(weight_coh)
            steer.add(coh)
        else:
            sep.mult(weight_sep)
            ali.mult(weight_ali)
            coh.mult(weight_coh)
            steer.add(sep); steer.add(ali); steer.add(coh)
        self.apply_force(steer)
        
    def rule_cohesion(self, others):
        center = PVector(0,0)
        count = 0
        for o in others:
            if o is self: continue
            if self.pos.dist(o.pos) < view_radius:
                center.add(o.pos)
                count += 1
        if count > 0:
            center.div(count)
            return self.steer_to(center)
        return PVector(0,0)

    def wrap_edges(self):
        if self.pos.x < 0: self.pos.x = width
        if self.pos.x > width: self.pos.x = 0
        if self.pos.y < 0: self.pos.y = height
        if self.pos.y > height: self.pos.y = 0
    
    
    def draw_boid(self):
        angle = self.vel.heading()
        pushMatrix()
        pushStyle()
        translate(self.pos.x, self.pos.y)
        rotate(angle)
        rectMode(CENTER)
        fill(230)
        stroke(40)
        rect(0, 0, 16, 6)
        popStyle()
        popMatrix()
        
    def draw_radius(self):
        if not show_radius: return
        pushStyle()
        noFill()
        stroke(120,120)
        ellipse(self.pos.x, self.pos.y, view_radius*2, view_radius*2)
        popStyle()

"""
This is the end of my custom class
"""

def add_boids(n):
    for b in range(n):
        flock.append(Boid(random(width), random(height)))


def setup():
    size(1980, 1080)
    frameRate(60)
    add_boids(30)
    

def clear_trail(a=60):
    pushMatrix()
    pushStyle()
    resetMatrix()
    noStroke()
    fill(18, 18, 24, a)
    rectMode(CORNER)
    rect(0, 0, width, height)
    popStyle()
    popMatrix()

    

def draw():
    
    if not running:
        clear_trail(10)
        for b in flock:
            b.draw_boid()
        return
    
    clear_trail(0)
    #first apply all rules to every agent
    for b in flock:
        b.apply_rules(flock)
    #then draw all the agents
    for b in flock: 
        b.update()
        b.wrap_edges()
        b.draw_boid()
        b.draw_radius()


def keyPressed():
    global show_radius
    global mode, show_info, running
    global view_radius, max_speed, max_force
    if key in ('s', 'S'):
        add_boids(20)
    elif key in ('c', 'C'):
        flock[:] = []
    elif key in ('v','V'): show_radius = not show_radius
    elif key == '1': mode = 'sep'
    elif key == '2': mode = 'ali'
    elif key == '3': mode = 'coh'
    elif key == '4': mode = 'all'
    elif key == ' ': running = not running #space
    elif key == '[': view_radius = max(10, view_radius - 5)
    elif key == ']': view_radius = min(200, view_radius + 5)
    elif key == 'a': max_speed = max(0.5, max_speed - 0.2)
    elif key == 'd': max_speed = min(8.0, max_speed + 0.2)
    elif key == 'f': max_force = max(0.005, max_force - 0.005)
    elif key == 'g': max_force = min(0.5, max_force + 0.005)
