mode = 'all'
show_info = True
running = True

view_radius = 70.0
max_speed = 3.0
max_force = 0.09
show_radius = False
weight_sep = 0.9
weight_ali = 2.0
weight_coh = 1.6

flock = []

flow_strength = 0.0
flow_center = None

surfaceY = 0
surfaceB = 8

dolphins = []

sardine_threat_radius = 320.0
sardine_escape_force = 0.55
sardine_escape_speed_mult_max = 8.0

restart = False

SARDINE_LEN = 18
SARDINE_W   = 9
DOLPHIN_LEN = 58
DOLPHIN_W   = 16

MIN_SEP = 18.0

DOLPHIN_SPEED = 4.8
DOLPHIN_FORCE = 0.26
DOLPHIN_VIEW  = 420.0
LEAD_TIME_MAX = 22.0
FLANK_GAIN    = 0.45
DOLPHIN_SEP_R = 60.0
DOLPHIN_SEP_W = 0.9

HERD_MARGIN = 90.0
ORBIT_AHEAD = 0.9
WEIGHT_REJOIN = 1.2

WRAP_MARGIN = 24.0

SPAWN_SARDINE_EVERY_FRAMES = 240
SPAWN_DOLPHIN_EVERY_FRAMES = 900
MAX_SARDINES = 120
MAX_DOLPHINS = 8

CAPTURE_R = 18.0
FRONT_CONE_DEG = 65.0
FRONT_CONE_COS = cos(radians(FRONT_CONE_DEG))
EAT_COOLDOWN_FRAMES = 10

pops = []

WATER_MAX = 2600
WATER_MIN_EMIT = 1
WATER_MAX_EMIT = 3
SARDINE_EMIT_MIN = 0
SARDINE_EMIT_MAX = 2

sardines_eaten = 0



class Pop(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.age = 0
        self.max_age = 22
        self.j = random(10000)
    def update(self):
        self.age += 1
    def done(self):
        return self.age >= self.max_age
    def draw(self):
        t = float(self.age) / self.max_age
        r = lerp(6, 32, t)
        a = int(lerp(200, 0, t))
        n = int(90 + 50*(1.0-t))
        pushStyle()
        noStroke()
        fill(0, a)
        for i in range(n):
            ang = TWO_PI * (i/float(n)) + noise(self.j+i*0.13, t*2.0)*0.3
            rr = r + (noise(self.j+i*1.7, t*3.1)-0.5)*6.0
            px = self.x + cos(ang)*rr
            py = self.y + sin(ang)*rr
            ellipse(px, py, 1.0, 1.0)
        popStyle()

class Dust(object):
    def __init__(self, x, y, vx, vy, sz, life, col):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.sz = sz
        self.life = life
        self.maxlife = life
        self.j = random(10000)
        self.col = col
    def update(self):
        n = noise(self.x*0.01, self.y*0.01, frameCount*0.01+self.j)
        a = (n-0.5)*0.3
        ca = cos(a); sa = sin(a)
        vx2 = self.vx*ca - self.vy*sa
        vy2 = self.vx*sa + self.vy*ca
        self.vx = lerp(self.vx, vx2, 0.4)
        self.vy = lerp(self.vy, vy2, 0.4)
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
    def done(self):
        return self.life <= 0
    def draw(self):
        t = 1.0 - float(self.life)/self.maxlife
        a = int(160*(1.0+t*0.1))
        r = self.sz*(1.0+t*0.4)
        pushStyle()
        noStroke()
        fill(self.col, a)
        ellipse(self.x, self.y, r, r)
        popStyle()

water = []

class Boid(object):
    def __init__(self, x, y):
        self.pos = PVector(x, y)
        self.vel = PVector.fromAngle(random(TWO_PI))
        self.vel.mult(random(1.0, max_speed))
        self.acc = PVector(0, 0)
        self.temp_max_speed = None
        self.is_dolphin = False
        self.phase = random(TWO_PI)
        self.phase_rate = random(0.01, 0.03)
        self.eat_cd = 0
    def apply_flow(self):
        if flow_center is None or flow_strength == 0.0: return
        toCenter = PVector.sub(flow_center, self.pos)
        toCenter.mult(flow_strength)
        self.acc.add(toCenter)
    def update(self):
        ms = self.temp_max_speed if self.temp_max_speed is not None else (DOLPHIN_SPEED if self.is_dolphin else max_speed)
        self.vel.add(self.acc)
        if self.vel.mag() > ms:
            self.vel.setMag(ms)
        self.pos.add(self.vel)
        self.acc.mult(0)
        self.phase += self.phase_rate
        if self.is_dolphin and self.eat_cd > 0:
            self.eat_cd -= 1
    def apply_force(self, f):
        self.acc.add(f)
    def steer_to(self, target, desired_speed=None, force_cap=None):
        desired = PVector.sub(target, self.pos)
        if desired.mag() == 0:
            return PVector(0,0)
        desired.setMag(desired_speed if self.is_dolphin else max_speed)
        steer = PVector.sub(desired, self.vel)
        cap = force_cap if force_cap is not None else (DOLPHIN_FORCE if self.is_dolphin else max_force)
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
        if self.is_dolphin: 
            return
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
        if self.pos.x < -WRAP_MARGIN:
            self.pos.x = width + WRAP_MARGIN
        elif self.pos.x > width + WRAP_MARGIN:
            self.pos.x = -WRAP_MARGIN
        if self.pos.y < -WRAP_MARGIN:
            self.pos.y = height + WRAP_MARGIN
        elif self.pos.y > height + WRAP_MARGIN:
            self.pos.y = -WRAP_MARGIN
    def draw_boid(self):
        ang = self.vel.heading()
        L, Wt = SARDINE_LEN, SARDINE_W
        tip = ( L*0.55, 0)
        bL  = (-L*0.55, -Wt*0.6)
        bR  = (-L*0.55,  Wt*0.6)
        pushMatrix(); pushStyle()
        translate(self.pos.x, self.pos.y)
        rotate(ang)
        noStroke()
        fill(120, 210)
        for _ in range(int(L*1.8)):
            u = random(0.0, 1.0)
            v = random(0.0, 1.0)
            if u + v > 1.0:
                u = 1.0 - u
                v = 1.0 - v
            x = tip[0] + u*(bL[0]-tip[0]) + v*(bR[0]-tip[0])
            y = tip[1] + u*(bL[1]-tip[1]) + v*(bR[1]-tip[1])
            jx = (noise(x*0.05, y*0.05, frameCount*0.03)-0.5)*1.0
            jy = (noise(x*0.05+9.1, y*0.05+3.7, frameCount*0.03)-0.5)*1.0
            ellipse(x + jx, y + jy, 1.2, 1.2)
        popStyle(); popMatrix()
    def draw_dolphin(self):
        ang = self.vel.heading()
        L, Wt = DOLPHIN_LEN, DOLPHIN_W
        tip = ( L*0.60, 0)
        bL  = (-L*0.55, -Wt*0.45)
        bR  = (-L*0.55,  Wt*0.45)
        pushMatrix(); pushStyle()
        translate(self.pos.x, self.pos.y)
        rotate(ang)
        noStroke()
        fill(0)
        for _ in range(int(L*2.6)):
            u = random(0.0, 1.0)
            v = random(0.0, 1.0)
            if u + v > 1.0:
                u = 1.0 - u
                v = 1.0 - v
            x = tip[0] + u*(bL[0]-tip[0]) + v*(bR[0]-tip[0])
            y = tip[1] + u*(bL[1]-tip[1]) + v*(bR[1]-tip[1])
            jx = (noise(x*0.04, y*0.04, frameCount*0.025)-0.5)*1.2
            jy = (noise(x*0.04+5.3, y*0.04+8.2, frameCount*0.025)-0.5)*1.2
            ellipse(x + jx, y + jy, 1.6, 1.6)
        popStyle(); popMatrix()
    def draw_radius(self):
        return

def spawn_from_edge(speed_min, speed_max, as_dolphin=False):
    edge = int(random(4))
    if edge == 0:
        x = -WRAP_MARGIN; y = random(height)
        dirv = PVector(1, random(-0.4, 0.4))
    elif edge == 1:
        x = width + WRAP_MARGIN; y = random(height)
        dirv = PVector(-1, random(-0.4, 0.4))
    elif edge == 2:
        x = random(width); y = -WRAP_MARGIN
        dirv = PVector(random(-0.4, 0.4), 1)
    else:
        x = random(width); y = height + WRAP_MARGIN
        dirv = PVector(random(-0.4, 0.4), -1)
    b = Boid(x, y)
    speed = random(speed_min, speed_max)
    dirv.normalize()
    b.vel = dirv.mult(speed)
    if as_dolphin:
        b.is_dolphin = True
        b.temp_max_speed = DOLPHIN_SPEED
        b.orbit_dir = 1 if random(1) < 0.5 else -1
        dolphins.append(b)
    else:
        flock.append(b)

def add_boids(n):
    for _ in range(n):
        spawn_from_edge(1.5, 2.8, as_dolphin=False)

def add_dolphin():
    spawn_from_edge(2.4, 4.0, as_dolphin=True)

def setup():
    size(1400, 800)
    frameRate(60)
    
    hudFont = createFont("Courier", 14);
    textFont(hudFont);
  
    global flow_center
    flow_center = PVector(width*0.5, height*0.55)
    global surfaceY
    surfaceY = height * 0.12
    add_boids(30)
    for _ in range(2):
        add_dolphin()

def clear_trail():
    pushMatrix(); pushStyle()
    resetMatrix()
    noStroke()
    fill(255)
    rectMode(CORNER)
    rect(0, 0, width, height)
    popStyle(); popMatrix()

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

def dolphin_separation_force(d):
    steer = PVector(0,0)
    count = 0
    for o in dolphins:
        if o is d: continue
        distv = d.pos.dist(o.pos)
        if distv < DOLPHIN_SEP_R and distv > 0:
            away = PVector.sub(d.pos, o.pos)
            away.normalize()
            away.mult((DOLPHIN_SEP_R - distv) / DOLPHIN_SEP_R)
            steer.add(away)
            count += 1
    if count > 0:
        steer.div(count)
        steer.setMag(DOLPHIN_FORCE * DOLPHIN_SEP_W)
    return steer

def handle_predation():
    global sardines_eaten
    if not dolphins or not flock:
        return
    to_remove = []
    for d in dolphins:
        if d.eat_cd > 0:
            continue
        if d.vel.mag() < 1e-6:
            fwd = PVector(1, 0)
        else:
            fwd = d.vel.get()
            fwd.normalize()
        best_idx = -1
        best_d = 1e9
        for i, s in enumerate(flock):
            distv = d.pos.dist(s.pos)
            if distv > CAPTURE_R:
                continue
            toS = PVector.sub(s.pos, d.pos)
            if toS.mag() < 1e-6:
                angle_ok = True
            else:
                toS.normalize()
                angle_ok = (fwd.dot(toS) >= FRONT_CONE_COS)
            if angle_ok and distv < best_d:
                best_d = distv
                best_idx = i
        if best_idx >= 0:
            sx, sy = flock[best_idx].pos.x, flock[best_idx].pos.y
            to_remove.append(best_idx)
            pops.append(Pop(sx, sy))
            d.eat_cd = EAT_COOLDOWN_FRAMES
            boost = d.vel.get()
            if boost.mag() > 0:
                boost.normalize()
                boost.mult(0.6)
                d.apply_force(boost)
    if to_remove:
        sardines_eaten += len(to_remove)
        to_remove.sort(reverse=True)
        for idx in to_remove:
            del flock[idx]

def emit_water_for_dolphin(d):
    spd = d.vel.mag()
    if spd < 0.1:
        return
    dirv = d.vel.get()
    dirv.normalize()
    bx = d.pos.x - dirv.x*(DOLPHIN_LEN*0.5)
    by = d.pos.y - dirv.y*(DOLPHIN_LEN*0.5)
    n = int(random(WATER_MIN_EMIT, WATER_MAX_EMIT+1))
    for _ in range(n):
        offx = random(-2.0, 2.0)
        offy = random(-2.0, 2.0)
        jx = -dirv.x*random(0.6, 1.6) + random(-0.3, 0.3)
        jy = -dirv.y*random(0.6, 1.6) + random(-0.3, 0.3)
        sz = random(1.0, 2.0)
        life = int(random(14, 28))
        water.append(Dust(bx+offx, by+offy, jx, jy, sz, life, 0))
    if len(water) > WATER_MAX:
        del water[:len(water)-WATER_MAX]

def emit_water_for_sardine(s):
    spd = s.vel.mag()
    if spd < 0.6:
        return
    dirv = s.vel.get()
    dirv.normalize()
    bx = s.pos.x - dirv.x*(SARDINE_LEN*0.55)
    by = s.pos.y - dirv.y*(SARDINE_LEN*0.55)
    n = int(random(SARDINE_EMIT_MIN, SARDINE_EMIT_MAX+1))
    for _ in range(n):
        offx = random(-1.0, 1.0)
        offy = random(-1.0, 1.0)
        jx = -dirv.x*random(0.4, 1.0) + random(-0.2, 0.2)
        jy = -dirv.y*random(0.4, 1.0) + random(-0.2, 0.2)
        sz = random(0.75, 1.25)
        life = int(random(10, 18))
        water.append(Dust(bx+offx, by+offy, jx, jy, sz, life, 80))
    if len(water) > WATER_MAX:
        del water[:len(water)-WATER_MAX]

def draw_hud():
    pushStyle()
    fill(0)
    textAlign(RIGHT, TOP)
    textSize(14)
    hdr = "# Dolphins: %d    Sardines eaten: %d" % (len(dolphins), sardines_eaten)
    text(hdr, width - 12, 10)
    textAlign(LEFT, BOTTOM)
    textSize(13)
    instructions = "D: spawn a dolphin    S: spawn sardines    R: restart"
    text(instructions, 12, height - 10)
    popStyle()

def draw():
    global restart
    if restart:
        restart = False
        reset_state()
    if not running:
        clear_trail()
        for b in flock:
            b.draw_boid()
        for d in dolphins:
            d.draw_dolphin()
        for p in list(pops):
            p.update(); p.draw()
            if p.done(): pops.remove(p)
        for wp in list(water):
            wp.update(); wp.draw()
            if wp.done(): water.remove(wp)
        draw_hud()
        return
    clear_trail()
    for b in flock:
        b.apply_rules(flock)
        nearestDist = 1e9
        nd = None
        for d in dolphins:
            distv = b.pos.dist(d.pos)
            if distv < nearestDist:
                nearestDist = distv
                nd = d
        if nd is not None:
            predict_t = min(LEAD_TIME_MAX, 14.0 / max(1.0, nd.vel.mag()))
            future = PVector(nd.pos.x + nd.vel.x * predict_t, nd.pos.y + nd.vel.y * predict_t)
            df = b.pos.dist(future)
            if df < sardine_threat_radius:
                away = PVector.sub(b.pos, future)
                if away.mag() > 1e-3:
                    away.normalize()
                    s = constrain((sardine_threat_radius - df)/sardine_threat_radius, 0, 1)
                    s2 = s*s
                    perp = PVector(-away.y, away.x)
                    perp.mult(0.35 * s2)
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
        b.update()
        b.wrap_edges()
        emit_water_for_sardine(b)
    resolve_sardine_collisions()
    center, base_r = flock_center_and_radius()
    for d in dolphins:
        target = None
        minD = DOLPHIN_VIEW
        for s in flock:
            ds = d.pos.dist(s.pos)
            if ds < minD:
                minD = ds
                target = s
        if target is not None:
            lead_t = min(LEAD_TIME_MAX, minD / max(1.0, DOLPHIN_SPEED + 0.001))
            future = PVector(target.pos.x + target.vel.x * lead_t,
                             target.pos.y + target.vel.y * lead_t)
            seek = d.steer_to(future, desired_speed=DOLPHIN_SPEED, force_cap=DOLPHIN_FORCE)
            toT = PVector.sub(future, d.pos)
            if toT.mag() > 0:
                toT.normalize()
                tangent = PVector(-toT.y, toT.x)
                tangent.mult(FLANK_GAIN * (1.0 + 0.25 * sin(d.phase)) * (1 if hasattr(d,'orbit_dir') and d.orbit_dir==1 else -1))
                flank = PVector.add(PVector.mult(toT, 0.6), tangent)
                flank.setMag(DOLPHIN_FORCE * 0.9)
                seek.add(flank)
            seek.add(dolphin_separation_force(d))
            d.apply_force(seek)
        else:
            desired_r = base_r + HERD_MARGIN + 20.0 * sin(d.phase*0.7)
            v = PVector.sub(d.pos, center)
            if v.mag() < 1e-3:
                v = PVector(random(-1,1), random(-1,1))
            ang = atan2(v.y, v.x)
            target_ang = ang + (d.orbit_dir if hasattr(d, 'orbit_dir') else 1) * (ORBIT_AHEAD + 0.25*sin(d.phase))
            tx = center.x + cos(target_ang) * desired_r
            ty = center.y + sin(target_ang) * desired_r
            seek = d.steer_to(PVector(tx, ty), desired_speed=DOLPHIN_SPEED, force_cap=DOLPHIN_FORCE)
            seek.add(dolphin_separation_force(d))
            d.apply_force(seek)
        d.temp_max_speed = DOLPHIN_SPEED
        d.update()
        d.wrap_edges()
        emit_water_for_dolphin(d)
    if frameCount % SPAWN_SARDINE_EVERY_FRAMES == 0 and len(flock) < MAX_SARDINES:
        for _ in range(int(random(2, 6))):
            spawn_from_edge(1.6, 3.0, as_dolphin=False)
    if frameCount % SPAWN_DOLPHIN_EVERY_FRAMES == 0 and len(dolphins) < MAX_DOLPHINS:
        add_dolphin()
    handle_predation()
    for wp in list(water):
        wp.update()
        wp.draw()
        if wp.done():
            water.remove(wp)
    for b in flock:
        b.draw_boid()
    for d in dolphins:
        d.draw_dolphin()
    for p in list(pops):
        p.update()
        p.draw()
        if p.done():
            pops.remove(p)
    draw_hud()

def reset_state():
    global flow_center, surfaceY, flock, dolphins, sardines_eaten
    flow_center = PVector(random(width), random(height))
    surfaceY = height * 0.12
    flock = []
    dolphins = []
    sardines_eaten = 0
    add_boids(30)
    for _ in range(2):
        add_dolphin()

def keyPressed():
    global show_radius
    global mode, show_info, running
    global view_radius, max_speed, max_force
    global restart
    if key in ('s', 'S'):
        add_boids(10)
    elif key in ('c', 'C'):
        flock[:] = []
    elif key in ('v','V'): show_radius = not show_radius
    elif key == '1': mode = 'sep'
    elif key == '2': mode = 'ali'
    elif key == '3': mode = 'coh'
    elif key == '4': mode = 'all'
    elif key == ' ': running = not running
    elif key == '[': view_radius = max(10, view_radius - 5)
    elif key == ']': view_radius = min(260, view_radius + 5)
    elif key == 'a': max_speed = max(0.5, max_speed - 0.2)
    elif key == 'f': max_force = max(0.005, max_force - 0.005)
    elif key == 'g': max_force = min(0.5, max_force + 0.005)
    elif key == 'd':
        add_dolphin()
    elif key == 'r':
        restart = True
