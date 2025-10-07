
# "d" to spawn more dolphins
# "r" to restart the whole thing entirely 
# "s" to spawn another group of sartine

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

flow_strength = 0.008
flow_center = None

surfaceY = 0
surfaceB = 8

dolphins = []


sardine_threat_radius = 140.0

sardine_escape_force = 0.10
sardine_escape_speed_mult_max = 2.0

restart = False



"""
This is the start of my custom class
"""

class Boid(object):
    def __init__(self, x, y):
        self.pos = PVector(x, y)
        self.vel = PVector.fromAngle(random(TWO_PI))
        self.vel.mult(random(1.0, max_speed))
        self.acc = PVector(0, 0)
        
        self.temp_max_speed = None
        
    def apply_flow(self):
        toCenter = PVector.sub(flow_center, self.pos)
        toCenter.mult(flow_strength)
        self.acc.add(toCenter)
        
        
    
    def update(self):
        
        ms = self.temp_max_speed if self.temp_max_speed is not None else max_speed
        self.vel.add(self.acc)
        if self.vel.mag() > ms:
            self.vel.setMag(ms)
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
        if self.pos.y < surfaceY:
            self.pos.y = surfaceY + surfaceB
            self.vel.y = abs(self.vel.y) * 0.8
        if self.pos.x < 0: self.pos.x = width
        if self.pos.x > width: self.pos.x = 0
        if self.pos.y > height: self.pos.y = 0
    
    
    def draw_boid(self):
        angle = self.vel.heading()
        pushMatrix()
        pushStyle()
        translate(self.pos.x, self.pos.y)
        rotate(angle)
        
        pushStyle()
        stroke(0)
        line(0, 0, 30, 0)
        popStyle()
        
        
        rectMode(CENTER)
        fill(230)
        stroke(40)
        rect(0, 0, 16, 6)
        popStyle()
        popMatrix()
        
    def draw_dolphin(self):
        angle = self.vel.heading()
        pushMatrix()
        pushStyle()
        translate(self.pos.x, self.pos.y)
        rotate(angle)
        
        pushStyle()
        stroke(0)
        line(0, 0, 30, 0)
        popStyle()
        
        
        rectMode(CENTER)
        fill(255,0,0)
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
        
        
def add_dolphin():
    d = Boid(random(width), random(surfaceY + 80, height - 60))
    d.vel.setMag(random(1.6, 3.8))
    dolphins.append(d)


def setup():
    
    size(1500, 860)
    frameRate(60)
    
    global flow_center
    flow_center = PVector(width*0.5, height*0.55)
    
    global surfaceY
    surfaceY = height * 0.1
    
    add_boids(30)
    
    for d in range(2):
        add_dolphin()

    

def clear_trail(a=0):
    pushMatrix()
    pushStyle()
    resetMatrix()
    noStroke()
    fill(18, 18, 24)
    rectMode(CORNER)
    rect(0, 0, width, height)
    popStyle()
    popMatrix()

    

def draw():
    global restart
    
    if restart:
        restart = False
        reset_state()
        
    if not running:
        clear_trail()
        for b in flock:
            b.draw_boid()
        return
    
    clear_trail(0)

    for b in flock:
        b.apply_rules(flock)
        
        # Sardine escape
        nearestD = None
        nearestDist = 1e9
        for d in dolphins:
            dist = b.pos.dist(d.pos)
            if dist < nearestDist:
                nearestDist = dist
                
                
        # escape force
        if nearestDist < sardine_threat_radius:
            
            # find the nearest dolphin again to push directly away
            for d in dolphins:
                if b.pos.dist(d.pos) == nearestDist:
                    away = PVector.sub(b.pos, d.pos)
                    if away.mag() > 1e-3:
                        away.normalize()
                        s = constrain((sardine_threat_radius - nearestDist)/sardine_threat_radius, 0, 1)
                        away.mult(s * sardine_escape_force)
                        b.apply_force(away)
                    break
                
                
            # shock speed boost
            shock = 1.0 - constrain(nearestDist / sardine_threat_radius, 0, 1)
            b.temp_max_speed = lerp(max_speed, max_speed * sardine_escape_speed_mult_max, shock)
        else:
            b.temp_max_speed = None
        

    #then draw all the agents
    for b in flock: 
        b.apply_rules(flock)
        b.apply_flow() 
        b.update()
        b.wrap_edges()
        b.draw_boid()
        b.draw_radius()

        
    for d in dolphins:
        
        d.apply_flow()
                
        d.update()
        d.wrap_edges()
        
        d.draw_dolphin()



def reset_state():
    global flow_center, surfaceY, flock, dolphins
    flow_center = PVector(random(width), random(height))
    surfaceY = height * 0.1

    flock= []
    dolphins= []

    add_boids(30)
    for _ in range(2):
        add_dolphin()



def keyPressed():
    global show_radius
    global mode, show_info, running
    global view_radius, max_speed, max_force
    global restart
    
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
    # elif key == 'd': max_speed = min(8.0, max_speed + 0.2)
    elif key == 'f': max_force = max(0.005, max_force - 0.005)
    elif key == 'g': max_force = min(0.5, max_force + 0.005)
    
    elif key == 'd':
        add_dolphin()

    elif key == 'r':
        restart = True
