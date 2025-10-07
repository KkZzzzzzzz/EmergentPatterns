mode = 'all'
show_info = True
running = True

view_radius = 60.0
max_speed = 3.0
max_force = 0.09
show_radius = True
weight_sep = 0.9
weight_ali = 2.0
weight_coh = 1.6

flock = []

flow_strength = 0.0
flow_center = None

surfaceY = 0
surfaceB = 8

dolphins = []

sardine_threat_radius = 260.0
sardine_escape_force = 0.26
sardine_escape_speed_mult_max = 4.2

restart = False

SARDINE_LEN = 15
SARDINE_W = 8
DOLPHIN_LEN = 30
DOLPHIN_W = 16

MIN_SEP = 18.0

DOLPHIN_SPEED = 4.6
DOLPHIN_FORCE = 0.24
HERD_MARGIN = 90.0
ORBIT_AHEAD = 0.9
WEIGHT_REJOIN = 1.2

EDGE_MARGIN = 100.0
EDGE_PUSH = 0.14
SURFACE_MARGIN = 140.0
SURFACE_PUSH = 0.24

DOLPHIN_EDGE_MARGIN = 220.0
DOLPHIN_EDGE_PUSH = 0.32
DOLPHIN_SURFACE_MARGIN = 160.0
DOLPHIN_SURFACE_PUSH = 0.38
SURFACE_BREACH = 20.0

class Boid(object):
    def __init__(self, x, y):
        self.pos = PVector(x, y)
        self.vel = PVector.fromAngle(random(TWO_PI))
        self.vel.mult(random(1.0, max_speed))
        self.acc = PVector(0, 0)
        self.temp_max_speed = None
        self.is_dolphin = False
        
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
        
    def steer_to(self, target, desired_speed=None, force_cap=None):
        desired = PVector.sub(target, self.pos)
        if desired.mag() == 0:
            return PVector(0,0)
        desired.setMag(desired_speed if desired_speed is not None else max_speed)
        steer = PVector.sub(desired, self.vel)
        cap = force_cap if force_cap is not None else max_force
        if steer.mag() > cap: steer.setMag(cap)
        return steer
    
    def rule_separation(self, others):
        steer = PVector(0, 0)
        count = 0
        for o in others:
            if o is self: continue
            d = self.pos.dist(o.pos)
            if d == 0 or d >= view_radius: continue
            if d < MIN_SEP:
                diff = PVector.sub(self.pos, o.pos)
                if diff.mag() > 0: diff.normalize()
                k = (MIN_SEP - d) / MIN_SEP
                diff.mult(k * 2.2)
                steer.add(diff)
                count += 1
        if count > 0:
            steer.div(count)
            steer.setMag(max_speed)
            steer.sub(self.vel)
            if steer.mag() > max_force: steer.setMag(max_force)
        return steer
    
    def rule_alignment(self, others):
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
        return PVector(0, 0)
    
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

    def rule_rejoin(self):
        c, r = flock_center_and_radius()
        d = self.pos.dist(c)
        if d > r * 1.05:
            return self.steer_to(c)
        return PVector(0,0)

    def apply_rules(self, others):
        sep = self.rule_separation(others)
        ali = self.rule_alignment(others)
        coh = self.rule_cohesion(others)
        rej = self.rule_rejoin()
        steer = PVector(0,0)
        if mode == 'sep':
            sep.mult(weight_sep); steer.add(sep)
        elif mode == 'ali':
            ali.mult(weight_ali); steer.add(ali)
        elif mode == 'coh':
            coh.mult(weight_coh); steer.add(coh)
        else:
            sep.mult(weight_sep); ali.mult(weight_ali); coh.mult(weight_coh); rej.mult(WEIGHT_REJOIN)
            steer.add(sep); steer.add(ali); steer.add(coh); steer.add(rej)
        self.apply_force(steer)

    def wrap_edges(self):
        if self.is_dolphin:
            if self.pos.x < 0:
                self.pos.x = 0
                self.vel.x = abs(self.vel.x)
            if self.pos.x > width:
                self.pos.x = width
                self.vel.x = -abs(self.vel.x)
            top_cap = surfaceY - SURFACE_BREACH
            if self.pos.y < top_cap:
                self.pos.y = top_cap
                if self.vel.y < 0: self.vel.y = abs(self.vel.y) + 0.6
            if self.pos.y > height:
                self.pos.y = height
                if self.vel.y > 0: self.vel.y = -abs(self.vel.y)
        else:
            if self.pos.x < 0:
                self.pos.x = 0
                self.vel.x = abs(self.vel.x)
            if self.pos.x > width:
                self.pos.x = width
                self.vel.x = -abs(self.vel.x)
            if self.pos.y < surfaceY:
                self.pos.y = surfaceY
                self.vel.y = abs(self.vel.y) * 0.8
            if self.pos.y > height:
                self.pos.y = height
                self.vel.y = -abs(self.vel.y)
    
    def draw_boid(self):
        ang = self.vel.heading()
        L, Wt = SARDINE_LEN, SARDINE_W
        tip = ( L*0.55, 0)
        bL  = (-L*0.45, -Wt*0.5)
        bR  = (-L*0.45,  Wt*0.5)
        pushMatrix(); pushStyle()
        translate(self.pos.x, self.pos.y)
        rotate(ang)
        noStroke()
        fill(230)
        triangle(tip[0], tip[1], bL[0], bL[1], bR[0], bR[1])
        stroke(40); noFill()
        triangle(tip[0], tip[1], bL[0], bL[1], bR[0], bR[1])
        popStyle(); popMatrix()
        
    def draw_dolphin(self):
        ang = self.vel.heading()
        L, Wt = DOLPHIN_LEN, DOLPHIN_W
        tip = ( L*0.55, 0)
        bL  = (-L*0.45, -Wt*0.5)
        bR  = (-L*0.45,  Wt*0.5)
        pushMatrix(); pushStyle()
        translate(self.pos.x, self.pos.y)
        rotate(ang)
        noStroke()
        fill(255,0,0)
        triangle(tip[0], tip[1], bL[0], bL[1], bR[0], bR[1])
        stroke(40); noFill()
        triangle(tip[0], tip[1], bL[0], bL[1], bR[0], bR[1])
        popStyle(); popMatrix()
        
    def draw_radius(self):
        if not show_radius: return
        pushStyle()
        noFill()
        stroke(120,120)
        ellipse(self.pos.x, self.pos.y, view_radius*2, view_radius*2)
        popStyle()

def add_boids(n):
    for b in range(n):
        y0 = random(max(surfaceY + SURFACE_MARGIN, 0), height - EDGE_MARGIN)
        x0 = random(EDGE_MARGIN, width - EDGE_MARGIN)
        flock.append(Boid(x0, y0))
        
def add_dolphin():
    d = Boid(random(width), random(surfaceY + DOLPHIN_SURFACE_MARGIN + 40, height - DOLPHIN_EDGE_MARGIN))
    d.vel.setMag(random(1.6, 3.8))
    d.orbit_dir = 1 if random(1) < 0.5 else -1
    d.is_dolphin = True
    dolphins.append(d)

def setup():
    size(1920, 1080)
    frameRate(60)
    global flow_center
    flow_center = PVector(width*0.5, height*0.55)
    global surfaceY
    surfaceY = height * 0.12
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

def resolve_sardine_collisions():
    n = len(flock)
    for i in range(n):
        bi = flock[i]
        for j in range(i+1, n):
            bj = flock[j]
            dx = bj.pos.x - bi.pos.x
            dy = bj.pos.y - bi.pos.y
            d2 = dx*dx + dy*dy
            if d2 == 0:
                dx = random(-1,1)
                dy = random(-1,1)
                d2 = dx*dx + dy*dy
            d = sqrt(d2)
            if d < MIN_SEP:
                overlap = (MIN_SEP - d) * 0.4
                nx = dx / d
                ny = dy / d
                bi.pos.x -= nx * overlap
                bi.pos.y -= ny * overlap
                bj.pos.x += nx * overlap
                bj.pos.y += ny * overlap

def flock_center_and_radius():
    if not flock:
        return PVector(width*0.5, height*0.5), 120.0
    c = PVector(0,0)
    for b in flock:
        c.add(b.pos)
    c.div(len(flock))
    r = 0.0
    for b in flock:
        r = max(r, b.pos.dist(c))
    if r < 80: r = 80
    return c, r

def apply_boundary_avoidance(b):
    fx = 0.0
    fy = 0.0
    if b.is_dolphin:
        if b.pos.x < DOLPHIN_EDGE_MARGIN:
            s = (DOLPHIN_EDGE_MARGIN - b.pos.x) / DOLPHIN_EDGE_MARGIN
            fx += DOLPHIN_EDGE_PUSH * s
        if b.pos.x > width - DOLPHIN_EDGE_MARGIN:
            s = (b.pos.x - (width - DOLPHIN_EDGE_MARGIN)) / DOLPHIN_EDGE_MARGIN
            fx -= DOLPHIN_EDGE_PUSH * s
        if b.pos.y > height - DOLPHIN_EDGE_MARGIN:
            s = (b.pos.y - (height - DOLPHIN_EDGE_MARGIN)) / DOLPHIN_EDGE_MARGIN
            fy -= DOLPHIN_EDGE_PUSH * s
        top_cap = surfaceY - SURFACE_BREACH
        if b.pos.y < top_cap + DOLPHIN_SURFACE_MARGIN:
            s = (top_cap + DOLPHIN_SURFACE_MARGIN - b.pos.y) / DOLPHIN_SURFACE_MARGIN
            fy += DOLPHIN_SURFACE_PUSH * s
    else:
        if b.pos.x < EDGE_MARGIN:
            s = (EDGE_MARGIN - b.pos.x) / EDGE_MARGIN
            fx += EDGE_PUSH * s
        if b.pos.x > width - EDGE_MARGIN:
            s = (b.pos.x - (width - EDGE_MARGIN)) / EDGE_MARGIN
            fx -= EDGE_PUSH * s
        if b.pos.y > height - EDGE_MARGIN:
            s = (b.pos.y - (height - EDGE_MARGIN)) / EDGE_MARGIN
            fy -= EDGE_PUSH * s
        if b.pos.y < surfaceY + SURFACE_MARGIN:
            s = (surfaceY + SURFACE_MARGIN - b.pos.y) / SURFACE_MARGIN
            fy += SURFACE_PUSH * s
    if fx != 0.0 or fy != 0.0:
        b.apply_force(PVector(fx, fy))

def draw_surface_line():
    pushStyle()
    stroke(120, 180, 220)
    strokeWeight(2)
    line(0, surfaceY, width, surfaceY)
    popStyle()

def draw():
    global restart
    if restart:
        restart = False
        reset_state()
    if not running:
        clear_trail()
        draw_surface_line()
        for b in flock:
            b.draw_boid()
        for d in dolphins:
            d.draw_dolphin()
        return
    clear_trail(0)
    draw_surface_line()
    for b in flock:
        apply_boundary_avoidance(b)
        b.apply_rules(flock)
        nearestDist = 1e9
        nd = None
        for d in dolphins:
            distv = b.pos.dist(d.pos)
            if distv < nearestDist:
                nearestDist = distv
                nd = d
        if nd is not None:
            predict_t = 14.0 / max(1.0, d.vel.mag())
            future = PVector(nd.pos.x + nd.vel.x * predict_t, nd.pos.y + nd.vel.y * predict_t)
            df = b.pos.dist(future)
            if df < sardine_threat_radius:
                away = PVector.sub(b.pos, future)
                if away.mag() > 1e-3:
                    away.normalize()
                    s = constrain((sardine_threat_radius - df)/sardine_threat_radius, 0, 1)
                    s2 = s*s
                    perp = PVector(-away.y, away.x)
                    perp.mult(0.45 * s2)
                    flee = PVector(away.x, away.y)
                    flee.mult(s2 * sardine_escape_force)
                    flee.add(perp)
                    b.apply_force(flee)
                shock = 1.0 - constrain(df / sardine_threat_radius, 0, 1)
                b.temp_max_speed = lerp(max_speed, max_speed * sardine_escape_speed_mult_max, shock)
            else:
                b.temp_max_speed = None
        else:
            b.temp_max_speed = None
    for b in flock: 
        b.apply_rules(flock)
        b.update()
        b.wrap_edges()
    resolve_sardine_collisions()
    for b in flock:
        b.draw_boid()
        b.draw_radius()
    center, base_r = flock_center_and_radius()
    for d in dolphins:
        apply_boundary_avoidance(d)
        desired_r = base_r + HERD_MARGIN
        v = PVector.sub(d.pos, center)
        if v.mag() < 1e-3:
            v = PVector(random(-1,1), random(-1,1))
        ang = atan2(v.y, v.x)
        target_ang = ang + (d.orbit_dir if hasattr(d, 'orbit_dir') else 1) * ORBIT_AHEAD
        tx = center.x + cos(target_ang) * desired_r
        ty = center.y + sin(target_ang) * desired_r
        seek = d.steer_to(PVector(tx, ty), desired_speed=DOLPHIN_SPEED, force_cap=DOLPHIN_FORCE)
        d.apply_force(seek)
        d.temp_max_speed = DOLPHIN_SPEED
        d.update()
        d.wrap_edges()
        d.draw_dolphin()

def reset_state():
    global flow_center, surfaceY, flock, dolphins
    flow_center = PVector(random(width), random(height))
    surfaceY = height * 0.12
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
    elif key == ' ': running = not running
    elif key == '[': view_radius = max(10, view_radius - 5)
    elif key == ']': view_radius = min(200, view_radius + 5)
    elif key == 'a': max_speed = max(0.5, max_speed - 0.2)
    elif key == 'f': max_force = max(0.005, max_force - 0.005)
    elif key == 'g': max_force = min(0.5, max_force + 0.005)
    elif key == 'd':
        add_dolphin()
    elif key == 'r':
        restart = True
