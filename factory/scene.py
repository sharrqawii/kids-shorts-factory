"""Reusable procedural Blender assets. All geometry is created in this file."""
import math
import random
import bpy
from mathutils import Vector
from .story import pose


def material(name, color, roughness=.7):
    rgb = [int(color[i:i+2],16)/255 for i in (0,2,4)]
    # Hex palette is sRGB; Blender node values are linear.
    rgb = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb,1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb,1)
    bsdf.inputs['Roughness'].default_value = roughness
    return mat


def empty(name, loc=(0,0,0), parent=None):
    obj = bpy.data.objects.new(name,None)
    bpy.context.collection.objects.link(obj)
    obj.location=loc
    obj.parent=parent
    return obj


def orb(name, loc, scale, mat, parent=None, segments=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=12, location=loc)
    obj=bpy.context.object
    obj.name=name
    obj.scale=scale
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons:
        polygon.use_smooth=True
    obj.parent=parent
    return obj


def rounded_box(name, loc, scale, mat, parent=None, bevel=.25):
    bpy.ops.mesh.primitive_cube_add(size=2, location=loc)
    obj=bpy.context.object
    obj.name=name
    obj.scale=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mod=obj.modifiers.new('Soft toy corners','BEVEL')
    mod.width=bevel
    mod.segments=4
    obj.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    obj.data.materials.append(mat)
    obj.parent=parent
    return obj


def curve(name, points, mat, radius=.018, parent=None):
    data=bpy.data.curves.new(name,'CURVE')
    data.dimensions='3D'
    data.bevel_depth=radius
    data.bevel_resolution=2
    spline=data.splines.new('BEZIER')
    spline.bezier_points.add(len(points)-1)
    for p,xyz in zip(spline.bezier_points,points):
        p.co=xyz
        p.handle_left_type='AUTO'
        p.handle_right_type='AUTO'
    obj=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    obj.parent=parent
    return obj


def make_pip(spec):
    """Stable named hierarchy; reuse this builder unchanged for future episodes."""
    mats={key:material('Pip '+key,value) for key,value in spec['palette'].items()}
    white=material('Eye glints','FFFFFF',.3)
    root=empty(spec['id'])
    root['asset_version']=spec['id']
    orb('Pip soft body',(0,.13,.87),spec['body_scale'],mats['fur'],root)
    orb('Pip belly',(0,-.30,.84),(.42,.18,.46),mats['muzzle'],root)
    feet=[]
    for x,y in [(-.39,.36),(.39,.36),(-.40,-.20),(.40,-.20)]:
        feet.append(rounded_box('Pip stubby foot',(x,y,.23),(.22,.26,.23),mats['fur'],root,.17))
    head=empty('Pip head pivot',(0,-.14,1.43),root)
    rounded_box('Pip broad head',(0,0,0),spec['head_scale'],mats['fur'],head,.36)
    for x in [-.46,.46]:
        orb('Pip tiny ear',(x,.01,.43),(.15,.11,.18),mats['fur'],head)
        orb('Pip inner ear',(x,-.091,.44),(.083,.032,.11),mats['ear'],head)
    rounded_box('Pip broad muzzle',(0,-.48,-.17),(.53,.30,.25),mats['muzzle'],head,.22)
    eyes=[]
    for x in [-.36,.36]:
        eye=orb('Pip eye',(x,-.516,.095),(.085,.053,.11),mats['eye'],head)
        eyes.append(eye)
        orb('Pip catchlight',(x-.018,-.563,.13),(.024,.013,.028),white,head,16)
        orb('Pip rosy cheek',(x*1.22,-.554,-.065),(.095,.027,.049),mats['blush'],head)
        orb('Pip nostril',(x*.42,-.773,-.12),(.038,.018,.026),mats['eye'],head,16)
    curve('Pip gentle smile',[(-.14,-.778,-.27),(0,-.795,-.30),(.14,-.778,-.27)],mats['eye'],.012,head)
    # Neckerchief and tiny flower pin are identity anchors across every episode.
    orb('Pip mint scarf',(0,-.055,1.035),(.60,.52,.095),mats['scarf'],root)
    rounded_box('Pip scarf tip',(.22,-.46,.93),(.12,.065,.19),mats['scarf'],root,.065)
    for i in range(5):
        a=i*math.tau/5
        orb('Pip flower petal',(-.19+.055*math.cos(a),-.53,1.035+.055*math.sin(a)),(.039,.025,.039),mats['pin'],root,16)
    orb('Pip flower center',(-.19,-.558,1.035),(.030,.017,.030),mats['muzzle'],root,16)
    return {'root':root,'head':head,'eyes':eyes,'feet':feet}


def make_berry():
    root=empty('Giant strawberry',(.98,.40,0))
    red=material('Strawberry coral','F34B64',.43)
    seed=material('Strawberry golden seeds','FFE3A0')
    green=material('Strawberry leaves','389B58')
    # A lathed, gently heart-shaped berry; wide shoulders and a rounded tip.
    profile=[(.10,.12),(.28,.43),(.58,.69),(1.0,.86),(1.40,.91),(1.74,.75),(1.93,.40),(1.97,.04)]
    verts=[]
    faces=[]
    sides=48
    for z,r in profile:
        for j in range(sides):
            a=math.tau*j/sides
            verts.append((r*math.cos(a),r*math.sin(a),z))
    for ring in range(len(profile)-1):
        for j in range(sides):
            a=ring*sides+j;b=ring*sides+(j+1)%sides
            faces.append((a,b,b+sides,a+sides))
    faces.extend([tuple(reversed(range(sides))),tuple(range((len(profile)-1)*sides,len(profile)*sides))])
    mesh=bpy.data.meshes.new('Original strawberry mesh')
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    obj=bpy.data.objects.new('Berry body',mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent=root
    obj.data.materials.append(red)
    for p in mesh.polygons:p.use_smooth=True
    mod=obj.modifiers.new('Rounded berry','SUBSURF');mod.levels=1
    for row,(z,r) in enumerate(profile[1:-1]):
        for j in range(11):
            a=math.tau*(j+.5*(row%2))/11
            obj=orb('Berry seed',(r*math.cos(a),r*math.sin(a),z),(.038,.021,.071),seed,root,12)
            obj.rotation_euler[2]=a-math.pi/2
    for i in range(7):
        a=math.tau*i/7
        leaf=orb('Berry crown leaf',(.31*math.cos(a),.31*math.sin(a),1.97),(.45,.16,.064),green,root)
        leaf.rotation_euler=(0,.16,a)
    curve('Berry stem',[(0,0,1.9),(.08,0,2.14),(.23,0,2.24)],green,.065,root)
    return root


def build_scene(spec, width=540, height=960, samples=12, threads=4):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.render.engine='CYCLES'
    scene.cycles.device='CPU'
    scene.cycles.samples=samples
    scene.cycles.use_denoising=True
    scene.cycles.denoising_use_gpu=False
    scene.cycles.denoising_prefilter='FAST'
    scene.cycles.denoising_quality='BALANCED'
    scene.cycles.max_bounces=3
    scene.cycles.diffuse_bounces=2
    scene.cycles.glossy_bounces=1
    scene.cycles.use_adaptive_sampling=True
    scene.cycles.adaptive_threshold=.10
    scene.render.threads_mode='FIXED';scene.render.threads=threads
    scene.render.resolution_x=width;scene.render.resolution_y=height
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.image_settings.color_mode='RGB'
    scene.render.image_settings.compression=15
    scene.render.use_persistent_data=True
    scene.render.fps=12;scene.frame_end=240
    scene.view_settings.view_transform='AgX'
    scene.view_settings.exposure=.65
    scene.world=bpy.data.worlds.new('Pastel daylight')
    scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.80,1,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
    grass=material('Meadow mint','A7DFA1')
    hill=material('Distant sage','78CBA6')
    cream=material('Warm ivory','FFF2CB')
    pink=material('Flower pink','EB89BC')
    yellow=material('Butter yellow','FFD667')
    leaf=material('Leaf green','5CAD74')
    wood=material('Tree peach','CFA17B')
    lavender=material('Tree lavender','B6A1DD')
    bpy.ops.mesh.primitive_plane_add(size=200)
    bpy.context.object.name='Seamless meadow';bpy.context.object.data.materials.append(grass)
    for x,y,s in [(-3.2,3.2,2),(2.5,4,2.6),(-.2,5,2)]:
        orb('Rolling hill',(x,y,-.3),(s,s,1.5),hill)
    for x,y,s,mat in [(-2.1,1.8,.9,pink),(2.3,2.1,1.1,lavender),(-3.2,4,.7,leaf)]:
        curve('Toy tree trunk',[(x,y,0),(x-.08,y,s),(x+.03,y,1.5*s)],wood,.13)
        for dx,dz in [(-.32,0),(.30,0),(0,.40)]:
            orb('Candy tree crown',(x+dx*s,y,1.65*s+dz*s),(.60*s,.50*s,.65*s),mat)
    rng=random.Random(17)
    for i in range(18):
        x=rng.uniform(-3,3);y=rng.uniform(-1.4,3.8)
        if -1.9<x<2 and y<1.4:continue
        z=.25+rng.random()*.16
        curve('Daisy stem',[(x,y,0),(x,y,z)],leaf,.018)
        for p in range(5):
            a=p*math.tau/5
            orb('Daisy petal',(x+.095*math.cos(a),y+.095*math.sin(a),z),(.075,.075,.033),cream,None,12)
        orb('Daisy center',(x,y,z+.023),(.06,.06,.045),yellow,None,12)
    for x,y in [(-1.7,-1.2),(-1.1,-1.6),(-.35,-1.9),(.45,-2.1)]:
        orb('Garden stepping stone',(x,y,.035),(.32,.23,.055),cream)
    pip=make_pip(spec)
    berry=make_berry()
    heartmat=material('Affection pink','F579A5')
    heart=empty('Floating heart',(.1,0,2.5))
    # Stylized heart built with a curve outline and lobes.
    orb('Heart left',(-.085,0,.075),(.125,.06,.125),heartmat,heart)
    orb('Heart right',(.085,0,.075),(.125,.06,.125),heartmat,heart)
    v=[(-.20,0,.065),(.20,0,.065),(0,0,-.19),(-.20,.06,.065),(.20,.06,.065),(0,.06,-.19)]
    m=bpy.data.meshes.new('Heart point');m.from_pydata(v,[],[(0,1,2),(5,4,3),(0,3,4,1),(1,4,5,2),(2,5,3,0)])
    ob=bpy.data.objects.new('Heart tip',m);bpy.context.collection.objects.link(ob);ob.parent=heart;ob.data.materials.append(heartmat)
    bpy.ops.object.camera_add(location=(2.5,-11.5,6.2))
    camera=bpy.context.object
    camera.rotation_euler=(Vector((0,0,1.2))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=7.5
    camera.data.lens=50;scene.camera=camera
    bpy.ops.object.light_add(type='AREA',location=(-3,-4,7))
    light=bpy.context.object;light.data.energy=650;light.data.shape='DISK';light.data.size=5
    light.rotation_euler=(Vector((0,0,.7))-light.location).to_track_quat('-Z','Y').to_euler()
    return {'scene':scene,'pip':pip,'berry':berry,'heart':heart}


def apply_pose(rig,t):
    state=pose(t);pip=rig['pip']
    pip['root'].location=(state['x'],state['y'],state['z'])
    pip['root'].rotation_euler=(0,state['lean'],state['turn'])
    pip['head'].rotation_euler=(0,state['head_tilt'],0)
    for i,foot in enumerate(pip['feet']):
        foot.rotation_euler[0]=state['walk']*(1 if i%2 else -1)
    for eye in pip['eyes']:eye.scale.z=.11*state['eye']
    rig['berry'].rotation_euler[1]=state['berry_wobble']
    rig['heart'].location=(.0,-.5,state['heart_z'])
    rig['heart'].scale=(state['heart'],)*3
