# MAXScript: V-Ray 7 Reference

Property names below were harvested from V-Ray 7.40.04 (update 4 hotfix 2) in 3ds Max 2025
with `getPropNames`. Names are exact and case-insensitive in MAXScript. Values shown are the
defaults. When a property is not listed here, run `getPropNames <instance>` or
`showProperties <instance>` in Max instead of guessing.

## Renderer: select, detect, and access V-Ray

```maxscript
-- Class names carry the version, so look them up instead of hardcoding
-- e.g. V_Ray_7__update_4_hotfix_2_DR2 and V_Ray_GPU_7__update_4_hotfix_2_DR2
fn vrayCpuClass = (
	local found
	for c in RendererClass.classes where (matchPattern (c as string) pattern:"V_Ray_*") \
		and not (matchPattern (c as string) pattern:"*GPU*") do found = c
	found
)
renderers.current = (vrayCpuClass())()      -- make V-Ray the production renderer
vr = renderers.current                       -- 402 properties, see below
isVRay = matchPattern (classOf vr as string) pattern:"V_Ray_*"
vrayVersion()                                -- #("7.40.04", "00000", "086169db")

-- All settings persist in the scene; read one, set one
vr.gi_on
vr.output_width = 1920; vr.output_height = 1080     -- only used when output_getsetsfrommax = false
```

## Renderer: image sampler and progressive / bucket

```maxscript
vr = renderers.current
vr.imageSampler_type = 3          -- 3 = Progressive, 1 = Bucket (0 and 2 are legacy)
-- Progressive
vr.progressive_minSamples = 1
vr.progressive_maxSamples = 100
vr.progressive_noise_threshold = 0.01
vr.progressive_max_render_time = 0.0      -- minutes, 0 = unlimited
-- Bucket
vr.twoLevel_baseSubdivs = 1
vr.twoLevel_fineSubdivs = 25
vr.twoLevel_threshold = 0.01
vr.twoLevel_bucket_width = 48; vr.twoLevel_bucket_height = 48
-- Shared
vr.imageSampler_shadingRate = 6
vr.filter_on = true
vr.filter_kernel = VRayLanczosFilter()    -- also VRayBoxFilter, VRayTriangleFilter, ...
vr.filter_size = 2.0
vr.dmc_lockNoisePattern = false
vr.dmc_subdivs_mult = 1.0
-- Render mask
vr.imageSampler_renderMask_type = 0       -- 0 none, texture / selected / include-exclude / layers / objectIDs
vr.imageSampler_renderMask_objectIDs = "1,2"
```

## Renderer: global illumination

```maxscript
vr = renderers.current
vr.gi_on = true
vr.gi_primary_type = 2           -- 0 Irradiance map, 2 Brute force, 3 Light cache
vr.gi_secondary_type = 3         -- 0 None, 2 Brute force, 3 Light cache
vr.gi_primary_multiplier = 1.0
vr.gi_secondary_multiplier = 1.0
vr.gi_refractCaustics = true
vr.gi_reflectCaustics = 1
vr.gi_ao_on = false; vr.gi_ao_amount = 0.8; vr.gi_ao_radius = 10.0
-- Brute force
vr.dmcgi_subdivs = 8; vr.dmcgi_depth = 3
-- Light cache
vr.lightcache_subdivs = 1000
vr.lightcache_sampleSize = 0.01
vr.lightcache_bounces = 100
vr.lightcache_retrace_on = true; vr.lightcache_retrace_threshold = 2.0
vr.lightcache_mode = 0                   -- 0 single frame, 1 fly-through, 2 from file, 3 progressive path tracing
vr.lightcache_loadFileName = ""; vr.lightcache_saveFileName = undefined
vr.lightcache_autoSave = false; vr.lightcache_autoSaveFileName = undefined
-- Irradiance map (legacy)
vr.gi_irradmap_preset = 5                -- 0 very low .. 5 custom
vr.gi_irradmap_minRate = -3; vr.gi_irradmap_maxRate = 0
vr.gi_irradmap_subdivs = 50; vr.gi_irradmap_interpSamples = 20
```

## Renderer: color mapping, environment overrides, camera effects

```maxscript
vr = renderers.current
vr.colorMapping_type = 6                 -- 0 Linear, 1 Exponential, 2 HSV exp, 3 Intensity exp,
                                         -- 4 Gamma, 5 Intensity gamma, 6 Reinhard
vr.colorMapping_gamma = 2.2
vr.colorMapping_darkMult = 1.0; vr.colorMapping_brightMult = 1.0
vr.colorMapping_adaptationOnly = 2       -- 0 color mapping and gamma, 1 none, 2 color mapping only
vr.colorMapping_clampOutput = false
vr.colorMapping_affectBackground = true
vr.options_rgbColorSpace = 1             -- 1 sRGB, 2 ACEScg

-- Environment overrides (V-Ray tab); 3ds Max Environment map is used otherwise
vr.environment_gi_on = true
vr.environment_gi_map = VRayBitmap HDRIMapName:"C:/hdri/sky.exr" maptype:2
vr.environment_gi_map_on = true
vr.environment_gi_color_multiplier = 1.0
vr.environment_rr_on = false             -- reflection/refraction override
vr.environment_rr_map = undefined
vr.environment_refract_on = false
vr.environment_secondaryMatte_on = false

-- Camera settings in the renderer (apply when no VRayPhysicalCamera is used)
vr.camera_type = 0                       -- 0 standard, 1 spherical, 2 cylindrical, 3 cylindrical ortho, 4 box, 5 fish eye, ...
vr.camera_overrideFOV = false; vr.camera_fov = 45.0
vr.dof_on = false; vr.dof_distance = 200.0; vr.dof_shutter = 5.0
vr.moblur_on = false; vr.moblur_duration = 0.5
vr.camera_autoExposure = false; vr.camera_autoWhiteBalance = 0
```

## Renderer: output, VFB, resumable rendering

```maxscript
vr = renderers.current
vr.output_on = true
vr.output_getsetsfrommax = true          -- false: use output_width / output_height below
vr.output_width = 1920; vr.output_height = 1080
vr.output_saveFile = false               -- V-Ray raw / VFB save; the 3ds Max Render Output is separate
vr.output_fileName = ""
vr.output_saveRawFile = false            -- multichannel EXR/VRIMG with all render elements
vr.output_rawFileName = "C:/renders/shot_.exr"
vr.output_rawExrUseHalf = true
vr.output_splitgbuffer = false           -- separate files per render element
vr.output_splitfilename = ""
vr.output_splitRGB = true; vr.output_splitAlpha = true
vr.output_resumableRendering = false
vr.output_progressiveAutoSave = 0.0      -- minutes
vr.output_separateFolders = false
vr.output_force32bit_3dsmax_vfb = false
vr.output_renderType = 0                 -- 0 view, region, crop, blowup, ...

-- Standard 3ds Max output still applies:
rendSaveFile = true
rendOutputFilename = "C:/renders/shot_.png"
renderWidth = 1920; renderHeight = 1080
render camera:$VRayCam001 outputwidth:1920 outputheight:1080 vfb:false
```

## Renderer: global options and overrides

```maxscript
vr = renderers.current
vr.options_lights = true; vr.options_hiddenLights = true; vr.options_shadows = true
vr.options_defaultLights = 2              -- 0 off, 1 on, 2 off with GI
vr.options_reflectionRefraction = true
vr.options_overrideDepth_on = false; vr.options_overrideDepth = 5
vr.options_maps = true; vr.options_filterMaps = true
vr.options_glossyEffects = true
vr.options_displacement = true
vr.options_dontRenderImage = false        -- true: only compute GI / light cache
vr.options_showGIOnly = false
vr.options_maxRayIntensity_on = true; vr.options_maxRayIntensity = 20.0
vr.options_probabilisticLights = 2; vr.options_probabilisticLightsCount = 8
vr.options_physicalMaterialAsVRayMtl = true
-- Override material (clay render)
vr.options_overrideMtl_on = true
vr.options_overrideMtl_mtl = VRayMtl name:"Clay" Diffuse:(color 180 180 180)
vr.options_overrideMtl_excl_type = 0
vr.excludeListOverrideMtl = #($Glass01, $Water01)   -- nodes to keep their own material
-- Displacement globals
vr.displacement_overrideMax = true; vr.displacement_edgeLength = 4.0
vr.displacement_maxSubdivs = 256; vr.displacement_amount = 1.0
-- System
vr.system_numThreads = 0                  -- 0 = all cores
vr.system_distributedRender = false
vr.system_region_x = 48; vr.system_region_y = 48
vr.system_frameStamp_on = false; vr.system_frameStamp_string = "V-Ray %vrayversion | file: %filename | frame: %frame"
vr.system_vrayLog_level = 3; vr.system_vrayLog_file = "%TEMP%\\VRayLog.txt"
vr.textures_memLimit = 4000               -- MB
```

## VRayMtl: core properties

```maxscript
m = VRayMtl name:"Wood"
-- Diffuse / opacity
m.Diffuse = (color 160 120 80)
m.diffuse_roughness = 0.0
m.selfIllumination = black; m.selfIllumination_multiplier = 1.0; m.selfIllumination_gi = false
-- Reflection
m.Reflection = white                      -- reflection color; white + fresnel = physically plausible
m.reflection_weight = 1.0
m.reflection_glossiness = 0.7             -- 1.0 = mirror
m.brdf_useRoughness = false               -- true: reflection_glossiness is treated as roughness
m.reflection_fresnel = true
m.reflection_IOR = 1.6; m.reflection_lockIOR = true   -- unlock to use a separate reflection IOR
m.reflection_metalness = 0.0              -- 1.0 for metals (use with a colored Reflection)
m.hilight_glossiness = 1.0; m.reflection_lockGlossiness = true
m.reflection_maxDepth = 8
m.reflection_affectAlpha = 0
m.brdf_type = 4                           -- 0 Phong, 1 Blinn, 2 Ward, 4 GGX (Microfacet GTR)
m.gtr_gamma = 2.0
m.anisotropy = 0.0; m.anisotropy_rotation = 0.0; m.anisotropy_channel = 1
-- Refraction
m.Refraction = black                      -- white = fully transparent
m.refraction_ior = 1.6
m.refraction_glossiness = 1.0
m.refraction_maxDepth = 8
m.refraction_affectShadows = true
m.refraction_affectAlpha = 0              -- 0 color only, 1 color+alpha, 2 all channels
m.refraction_fogColor = white; m.refraction_fogMult = 1.0; m.refraction_fogDepth = 1.0
m.refraction_dispersion_on = false; m.refraction_dispersion = 50.0
m.refraction_thinWalled = false
-- Translucency (SSS)
m.translucency_on = 0                     -- 0 none, 1 volumetric, 2 SSS
m.translucency_amount = 1.0; m.translucency_color = white; m.translucency_scatterCoeff = 0.0
-- Coat / sheen / thin film
m.coat_amount = 0.0; m.coat_color = white; m.coat_glossiness = 1.0; m.coat_ior = 1.6
m.sheen_color = black; m.sheen_glossiness = 0.8
m.thinFilm_on = false; m.thinFilm_thickness_min = 250.0; m.thinFilm_thickness_max = 400.0
-- Options
m.option_doubleSided = true
m.option_reflectOnBack = false
m.option_opacityMode = 2                  -- 0 normal, 1 clip, 2 stochastic
m.option_cutOff = 0.001
m.option_traceReflection = true; m.option_traceRefraction = true
m.effect_id = 0; m.override_effect_id = false
m.preSet = 0
```

## VRayMtl: texture map slots (texmap_*)

Every slot has three properties: `texmap_<slot>` (the map), `texmap_<slot>_on` (bool), and
`texmap_<slot>_multiplier` (0-100 percent, default 100). `texmap_environment` has no multiplier.

```maxscript
m = VRayMtl name:"Concrete"
m.texmap_diffuse = VRayBitmap HDRIMapName:"C:/tex/concrete_albedo.jpg"
m.texmap_reflectionGlossiness = VRayBitmap HDRIMapName:"C:/tex/concrete_gloss.jpg"
m.texmap_bump = VRayNormalMap normal_map:(VRayBitmap HDRIMapName:"C:/tex/concrete_normal.png")
m.texmap_bump_multiplier = 100.0
m.texmap_displacement = VRayBitmap HDRIMapName:"C:/tex/concrete_height.png"
m.texmap_displacement_multiplier = 100.0
m.texmap_opacity = undefined
m.texmap_metalness = undefined
m.texmap_roughness = undefined            -- only used with brdf_useRoughness = true

-- Full slot list (V-Ray 7): diffuse, reflection, refraction, bump, reflectionGlossiness,
-- refractionGlossiness, refractionIOR, displacement, translucent, translucency_amount,
-- environment, hilightGlossiness, reflectionIOR, opacity, roughness, anisotropy,
-- anisotropy_rotation, refraction_fog, refraction_fog_depth, self_illumination,
-- gtr_tail_falloff, metalness, sheen, sheen_glossiness, coat_color, coat_amount,
-- coat_glossiness, coat_ior, coat_bump, coat_darkening, coat_anisotropy,
-- coat_anisotropy_rotation, thinFilm_thickness, thinFilm_ior

-- Turn a slot off without removing the map
m.texmap_bump_on = false

-- Assign to nodes
$Wall01.material = m
for n in selection do n.material = m
```

## Other V-Ray materials

```maxscript
-- VRayBlendMtl: base plus up to 9 coat layers (index 0..8)
b = VRayBlendMtl name:"Layered"
b.baseMtl = VRayMtl name:"Base"
b.coatMtl_0 = VRayMtl name:"Dust"
b.blend_0 = (color 127.5 127.5 127.5)     -- blend amount as color
b.texmap_blend_0 = VRayBitmap HDRIMapName:"C:/tex/dust_mask.png"
b.coatMtl_enable[1] = true                -- array form, 1-based
b.additiveMode = false

-- VRay2SidedMtl: thin translucent surfaces (leaves, paper, curtains)
t = VRay2SidedMtl frontMtl:(VRayMtl name:"Leaf") backMtlOn:false
t.translucency = (color 127.5 127.5 127.5)
t.texmap_translucency = undefined

-- VRayLightMtl: emissive surfaces
e = VRayLightMtl name:"Screen" color:white multiplier:5.0 twoSided:false
e.texmap = VRayBitmap HDRIMapName:"C:/tex/screen.png"; e.texmap_on = true
e.directLight_on = false                  -- true: also acts as a mesh light
e.opacity_texmap = undefined

-- VRayOverrideMtl: different materials for GI, reflections, refractions, shadows
o = VRayOverrideMtl baseMtl:m
o.giMtl = VRayMtl Diffuse:(color 200 200 200); o.giMtl_on = true
o.reflectMtl = undefined; o.refractMtl = undefined; o.shadowMtl = undefined

-- VRayMtlWrapper: matte/shadow and GI contribution controls
w = VRayMtlWrapper baseMtl:m
w.matteSurface = true; w.alphaContribution = -1.0
w.matte_shadows = true; w.matte_shadowsAffectAlpha = true
w.generateGI = true; w.receiveGI = true; w.generateGIMult = 1.0; w.receiveGIMult = 1.0

-- Others: VRayCarPaintMtl2, VRayHairNextMtl, VRayFastSSS2, VRayALSurfaceMtl,
-- VRaySwitchMtl, VRayScannedMtl, VRayPluginNodeMtl
```

## V-Ray texture maps: VRayBitmap / VRayHDRI

`VRayHDRI` is the same class as `VRayBitmap` (43 identical properties). Prefer it over
`Bitmaptexture` for V-Ray scenes: it handles HDR, gamma, UDIM, and tiled EXR.

```maxscript
bm = VRayBitmap HDRIMapName:"C:/tex/albedo.jpg"      -- the file path property
bm.maptype = 4                  -- 0 angular, 1 cubic, 2 spherical, 3 mirror ball, 4 explicit map channel (UVW)
bm.mapChannel = 1
bm.gamma = 1.0                  -- with color_space
bm.color_space = 4              -- 0 none, 1 inverse gamma, 2 sRGB, 4 auto (default)
bm.rgbColorSpace = 0
bm.multiplier = 1.0; bm.renderMultiplier = 1.0
bm.interpType = 3               -- 0 bilinear, 1 bicubic, 2 biquadratic, 3 default
bm.filterMode = 2               -- 0 nearest, 1 no filtering, 2 elliptical
bm.horizontalFlip = false; bm.verticalFlip = false
bm.horizontalRotation = 0.0     -- degrees, useful for dome/spherical HDRI
bm.cropplace_on = false; bm.cropplace_u = 0.0; bm.cropplace_v = 0.0; bm.cropplace_width = 1.0
bm.rgbOutput = 0; bm.monoOutput = 0; bm.alphaSource = 0
bm.udim_u_tile = 1; bm.udim_v_tile = 1
bm.ground_on = false; bm.ground_position = [0,0,0]; bm.ground_radius = 1000.0
bm.coords.U_Tiling = 2.0; bm.coords.V_Tiling = 2.0     -- standard UVW placement sub-object
bm.output.output_amount = 1.0                           -- standard Output sub-object

-- Spherical HDRI as environment
env = VRayBitmap HDRIMapName:"C:/hdri/sky.exr" maptype:2 horizontalRotation:90.0
environmentMap = env; useEnvironmentMap = true
```

## V-Ray texture maps: normal, dirt, triplanar, randomization, utility

```maxscript
-- VRayNormalMap: use in the bump slot
nm = VRayNormalMap normal_map:(VRayBitmap HDRIMapName:"C:/tex/normal.png")
nm.normal_map_multiplier = 1.0
nm.bump_map = undefined; nm.bump_map_multiplier = 1.0   -- optional extra height bump
nm.flip_green = false; nm.flip_red = false; nm.swap_red_and_green = false
nm.Map_Channel = 1; nm.apply_gamma = false

-- VRayDirt: ambient occlusion / dirt
d = VRayDirt radius:10.0 occluded_color:black unoccluded_color:white
d.distribution = 1.0; d.falloff = 0.0; d.subdivs = 3
d.mode = 0                      -- 0 AO, 1 reflection occlusion (Phong), 2 Blinn, 3 Ward, 4 inner, 5 ambient+inner
d.ignore_for_gi = true; d.consider_same_object_only = false
d.texmap_radius = undefined; d.texmap_occluded_color = undefined
d.excludeList = #()

-- VRayTriplanarTex: projection without UVs
tp = VRayTriplanarTex texture:(VRayBitmap HDRIMapName:"C:/tex/rock.jpg")
tp.size = 1.0; tp.Blend = 0.1
tp.texture_mode = 0             -- 0 same texture on all axes, 1 different per axis (texture_y, texture_z)
tp.space = 0                    -- 0 object, 1 world, 2 reference node
tp.random_texture_offset = true; tp.random_texture_rotation = true; tp.random_mode = 5

-- VRayUVWRandomizer: per-object / per-tile variation
ur = VRayUVWRandomizer seed:0
ur.mode_by_object_id = true; ur.mode_by_node_handle = false
ur.variance_u_min = 0.0; ur.variance_u_max = 1.0
ur.variance_rot_min = 0.0; ur.variance_rot_max = 360.0
ur.variance_uscale_min = 80.0; ur.variance_uscale_max = 120.0   -- percent
bmRand = VRayBitmap HDRIMapName:"C:/tex/planks.jpg" mapSource:ur

-- VRayMultiSubTex: color/texture per ID or random per object
ms = VRayMultiSubTex from_id:0
ms.random_by_node_handle = true; ms.random_hue = 0.05
ms.texmap_color[1] = red; ms.texmap[2] = VRayBitmap HDRIMapName:"C:/tex/a.jpg"

-- VRayColor: constant color with temperature/gamma
c = VRayColor color:(color 200 100 50) rgb_multiplier:1.0 alpha:1.0
c.color_mode = 0                -- 0 color, 1 temperature (use .temperature)

-- VRayEdgesTex: wireframe / rounded corners (put in bump)
edges = VRayEdgesTex thickness:0.1 widthType:1
edges.roundedCorners_radius = 0.5; edges.roundedCorners_sameObjectOnly = true

-- VRayDistanceTex: blend by distance to objects
dt = VRayDistanceTex objects:#($Road01) distance:10.0 near_color:black far_color:white

-- VRaySky: procedural sky, usually driven by a VRaySun
sky = VRaySky sun_node:$VRaySun001 manual_sun_node:true sky_model:5
environmentMap = sky; useEnvironmentMap = true
```

## Lights: VRayLight (plane, dome, sphere, mesh, disc)

```maxscript
-- Create lights as scene nodes
L = VRayLight type:0 pos:[0,0,300] name:"Key"
L.type = 0                      -- 0 plane, 1 dome, 2 sphere, 3 mesh, 4 disc
L.on = true
L.multiplier = 30.0
L.normalizeColor = 0            -- units: 0 default (image), 1 lm, 2 lm/m2/sr, 3 W, 4 W/m2/sr
L.color = white
L.color_mode = 0; L.color_temperature = 6500.0   -- color_mode 1 = temperature
L.sizeLength = 20.0; L.sizeWidth = 20.0          -- plane / disc
L.size0 = 10.0                                    -- sphere radius
L.castShadows = true; L.invisible = false; L.DoubleSided = false
L.affect_diffuse = true; L.affect_specular = true; L.affect_reflections = true
L.diffuse_contribution = 1.0; L.specular_contribution = 1.0
L.noDecay = false
L.skylightPortal = false; L.simplePortal = false
L.subdivs = 8; L.ShadowBias = 0.02; L.cutoffThreshold = 0.001
L.texmap = undefined; L.texmap_on = true; L.texmap_resolution = 512
L.excludeList = #($Floor01); L.inclExclType = 3
L.targeted = false; L.target_distance = 200.0
L.enable_viewport_shading = true
-- Aim a plane light: it emits along its local -Z; use a target or rotate the node
L.rotation = eulerAngles -90 0 0

-- Dome light with HDRI
dome = VRayLight type:1 name:"Dome" pos:[0,0,0]
dome.texmap = VRayBitmap HDRIMapName:"C:/hdri/sky.exr" maptype:2
dome.texmap_on = true; dome.multiplier = 1.0
dome.dome_spherical = true; dome.dome_affect_alpha = false
dome.invisible = false          -- true hides the HDRI from the camera
dome.dome_adaptive = false; dome.dome_finite = false; dome.dome_emitRadius = 150.0

-- Mesh light
ml = VRayLight type:3 mesh_source:$Neon01 mesh_replaceOnPick:true multiplier:50.0
```

## Lights: VRaySun, VRaySky, VRayIES, VRayAmbientLight

```maxscript
-- VRaySun: direction comes from the node/target position; sky from VRaySky map
sun = VRaySun name:"Sun" pos:[1000,-1000,1500]
sun.target = Targetobject pos:[0,0,0]
sun.enabled = true
sun.intensity_multiplier = 1.0; sun.size_multiplier = 1.0
sun.filter_Color = white; sun.color_mode = 0
sun.turbidity = 2.5; sun.ozone = 0.35; sun.water_vapour = 2.0
sun.sky_model = 5               -- 0 Preetham, 1 CIE clear, 2 CIE overcast, 3 Hosek, 4 PRG clear sky, 5 PRG clear sky new
sun.ground_albedo = (color 51 51 51)
sun.invisible = false; sun.shadow_subdivs = 3; sun.shadow_bias = 0.02
sun.affect_diffuse = true; sun.affect_specular = true; sun.affect_atmospherics = true
sun.clouds_on = false; sun.cloud_density = 0.5; sun.clouds_density_multiplier = 1.0
sun.cloud_variety = 0.3; sun.cirrus_amount = 0.2; sun.ground_shadows = false
sun.stars_on = false; sun.moon_on = false
sun.excludeList = #()

-- VRayIES: photometric profile
ies = VRayIES pos:[0,0,250] name:"Spot01"
ies.ies_file = "C:/ies/downlight.ies"
ies.power = 1700.0; ies.intensity_type = 0; ies.override_intensity = 0
ies.color_mode = 0; ies.color = white; ies.color_temperature = 6500.0
ies.targeted = true; ies.target_distance = 200.0
ies.use_light_shape = 1; ies.shape_subdivs = 8; ies.cast_shadows = true
ies.rotation_X = 0.0; ies.rotation_Y = 0.0; ies.rotation_Z = 0.0

-- VRayAmbientLight: cheap fill (19 props, e.g. .enabled, .color, .intensity)
-- Query lights
vrLights = for n in lights where (matchPattern (classOf n as string) pattern:"VRay*") collect n
```

## Camera: VRayPhysicalCamera

```maxscript
cam = VRayPhysicalCamera name:"Cam01" pos:[500,-800,170]
cam.targeted = true; cam.target = Targetobject pos:[0,0,120]   -- or cam.target_distance
cam.type = 0                    -- 0 still, 1 cinematic, 2 video
cam.film_width = 36.0; cam.focal_length = 40.0; cam.zoom_factor = 1.0
cam.specify_fov = false; cam.fov = 10.0            -- degrees when specify_fov = true
-- Exposure
cam.exposure = 1                -- 0 no exposure, 1 physical (ISO / f-number / shutter), 2 exposure value
cam.ISO = 100.0; cam.f_number = 8.0; cam.shutter_speed = 200.0   -- 1/200 s
cam.exposure_value = 13.0       -- used when exposure = 2
cam.whiteBalance_preset = 4; cam.whiteBalance = white; cam.temperature = 6500.0
cam.vignetting = false; cam.vignetting_amount = 1.0
-- Focus / DOF / motion blur
cam.use_dof = false
cam.specify_focus = true; cam.focus_distance = 800.0; cam.focus_node = undefined
cam.use_blades = false; cam.blades_number = 5
cam.use_moblur = 0; cam.shutter_angle = 180.0
-- Lens shift and tilt (architecture: vertical lines)
cam.vertical_shift = 0.0; cam.horizontal_shift = 0.0
cam.lens_tilt_auto = true       -- auto vertical tilt correction
cam.distortion = 0.0; cam.distortion_type = 0
-- Clipping and per-camera resolution
cam.clip_on = false; cam.clip_near = 0.0; cam.clip_far = 1000.0
cam.override_resolution = false; cam.override_width = 1920; cam.override_height = 1080
cam.horizon_on = false; cam.show_camera_cone = 0
viewport.setCamera cam
```

## Geometry: VRayProxy, VRayPlane, VRayFur, VRayClipper, VRayDecal, VRayScene

```maxscript
-- VRayProxy: load .vrmesh / .abc (export is done from the UI or vrmesh tools)
px = VRayProxy filename:"C:/assets/tree.vrmesh" name:"Tree01"
px.display = 3                  -- 0 bounding box, 1 preview from file, 2 point, 3 full (preview faces)
px.proxy_scale = 1.0; px.flip_axis = false
px.anim_type = 0; px.anim_speed = 1.0; px.anim_offset = 0.0
px.override_mtl = #(); px.override_rule = #()
px.material = VRayMtl name:"TreeMtl"
-- Alembic layers
px.abc_layer_on[1] = true; px.abc_layer_file[1] = "C:/assets/tree_layer.abc"

-- VRayPlane: infinite ground plane
ground = VRayPlane name:"Ground" pos:[0,0,0]
ground.material = VRayMtl Diffuse:(color 120 120 120)

-- VRayFur
fur = VRayFur sourceNode:$Rug01 length:15.0 thickness:0.2 gravity:-3.0 Bend:1.0
fur.numSides = 3; fur.numKnots = 8; fur.Taper = 0.0
fur.distribution = 1; fur.perFace = 1; fur.perArea = 0.2   -- distribution 0 per face, 1 per area
fur.lengthVar = 0.2; fur.thicknessVar = 0.2; fur.gravityVar = 0.2; fur.directionVar = 0.2
fur.map_length = undefined; fur.map_density = undefined; fur.map_direction = undefined
fur.viewport_maxHairs = 1000

-- VRayClipper: cut geometry at render time (section views)
clip = VRayClipper pos:[0,0,150] name:"Section"
clip.enabled = true; clip.affectLight = true; clip.onlyCameraRays = false
clip.fill_cavities = true; clip.useObjMtl = false; clip.setMaterialID = false
clip.enable_mesh_mode = false; clip.mesh_source = undefined
clip.excludeList = #(); clip.includeList = undefined

-- VRayDecal: projected material
dec = VRayDecal width:100.0 length:50.0 projection_depth:5.0 name:"Poster"
dec.material = VRayMtl name:"PosterMtl"
dec.Mask = undefined; dec.Bend = 0.0; dec.order = 0; dec.back_side = true

-- VRayScene: reference a .vrscene
sc = VRayScene scenefilePath:"C:/assets/car.vrscene" name:"Car"
sc.enabled = true; sc.flipAxis = 1; sc.addLights = true; sc.previewType = 1
```

## Modifiers: VRayDisplacementMod, VRayEnmeshMod

```maxscript
-- Displacement modifier (preferred over the VRayMtl displacement slot for control)
dm = VRayDisplacementMod()
addModifier $Terrain01 dm
dm.type = 1                     -- 0 2D mapping, 1 3D mapping, 2 subdivision
dm.texmap = VRayBitmap HDRIMapName:"C:/tex/height.exr"
dm.amount = 5.0; dm.shift = 0.0; dm.texmapChannel = 1
dm.waterLevelOn = false; dm.waterLevelValue = 0.0
dm.edgeLength = 4.0; dm.viewDependent = true; dm.maxSubdivs = 256; dm.minSubdivs = 8
dm.tightBounds = true; dm.keepContinuity = false
dm.smoothUVs = false; dm.catmullClark = false; dm.staticGeometry = true
dm.vectorDisplacement = 0       -- 0 off, 1 tangent, 2 object, 3 absolute tangent
dm.useObjectMtl = false         -- true: use the material's displacement map
dm.texmap_min = 0.0; dm.texmap_max = 1.0

-- Enmesh: tile a mesh over a surface at render time
em = VRayEnmeshMod()
addModifier $Fence01 em
em.objects = #($Tile01)
em.tiling_u = 5.0; em.tiling_v = 5.0; em.height = 100.0; em.height_offset = 50.0
em.rotation = 0.0; em.random_rotation = 0.0; em.use_random_rotation_steps = false
em.Map_Channel = 1; em.use_mesh_uvw_mapping = false
```

## Render elements

```maxscript
-- Manager API is the standard 3ds Max one
rem = maxOps.GetCurRenderElementMgr()
rem.RemoveAllRenderElements()
rem.AddRenderElement (VRayLighting elementName:"VRayLighting")
rem.AddRenderElement (VRayGlobalIllumination elementName:"VRayGlobalIllumination")
rem.AddRenderElement (VRayReflection elementName:"VRayReflection")
rem.AddRenderElement (VRayRefraction elementName:"VRayRefraction")
rem.AddRenderElement (VRaySpecular elementName:"VRaySpecular")
rem.AddRenderElement (VRayZDepth elementName:"VRayZDepth")
rem.AddRenderElement (VRayCryptomatte elementName:"VRayCryptomatte")
rem.AddRenderElement (VRayDenoiser elementName:"VRayDenoiser")
rem.SetElementsActive true
for i = 0 to rem.NumRenderElements() - 1 do (
	local e = rem.GetRenderElement i
	format "% enabled=%\n" (classOf e) e.enabled
)
-- Light select: one element per light or light group
ls = VRayLightSelect elementName:"Key_Select"
rem.AddRenderElement ls
-- Extra tex: render any map (e.g. VRayDirt) as an element
et = VRayExtraTex elementName:"AO"
rem.AddRenderElement et
et.texture = VRayDirt radius:20.0

-- Available V-Ray 7 element classes:
-- VRayAlpha VRayAO VRayAtmosphere VRayBackground VRayBackToBeauty VRayBumpNormals VRayCaustics
-- VRayCoatFilter VRayCoatGlossiness VRayCoatReflection VRayCoatSpecular VRayCryptomatte VRayDenoiser
-- VRayDiffuseFilter VRayDRBucket VRayEnhancerData VRayExtraTex VRayGlobalIllumination VRayIlluminance
-- VRayLighting VRayLightingAnalysis VRayLightMix VRayLightSelect VRayMatteShadow VRayMetalness
-- VRayMtlID VRayMtlReflectGlossiness VRayMtlReflectHilightGlossiness VRayMtlReflectIOR
-- VRayMtlRefractGlossiness VRayMtlSelect VRayNoiseLevel VRayNormals VRayObjectID VRayObjectSelect
-- VRayOptionRE VRayRawCoatFilter VRayRawCoatReflection VRayRawDiffuseFilter VRayRawGlobalIllumination
-- VRayRawLighting VRayRawReflection VRayRawReflectionFilter VRayRawRefraction VRayRawRefractionFilter
-- VRayRawShadow VRayRawSheenFilter VRayRawSheenReflection VRayRawTotalLighting VRayReflection
-- VRayReflectionFilter VRayRefraction VRayRefractionFilter VRayRenderID VRayRenderTime VRayRoughness
-- VRaySampleRate VRaySamplerInfo VRaySelfIllumination VRayShadows VRaySheenFilter VRaySheenGlossiness
-- VRaySheenReflection VRaySheenSpecular VRaySpecular VRaySSS2 VRayToonRenderElement VRayTotalLighting
-- VRayUnclampedColor VRayVelocity VRayWireColor VRayZDepth
```

## Common patterns and pitfalls

```maxscript
-- Detect V-Ray materials in the scene
vrMats = for m in sceneMaterials where classOf m == VRayMtl collect m
-- Convert Physical materials: V-Ray renders them natively (options_physicalMaterialAsVRayMtl),
-- or use the Scene Converter (Rendering > Scene Converter) for a true conversion.

-- Interactive rendering toggles live in the renderer, not the VFB:
vr = renderers.current
vr.ipr_progressiveMode = true; vr.ipr_fitToVFB = true

-- Object-level V-Ray properties (visible to camera / GI / reflections, matte) are edited
-- through the V-Ray Object Properties dialog; MAXScript access goes through the node's
-- user properties or the VRayMtlWrapper material.

-- Never assume a property name: V-Ray renames between versions.
getPropNames (VRayMtl())           -- 212 entries in V-Ray 7
getPropNames renderers.current     -- 402 entries
showProperties $VRayLight001

-- Class name checks must tolerate the version suffix
isVRayRenderer = matchPattern (classOf renderers.current as string) pattern:"V_Ray_*"
isVRayGPU = matchPattern (classOf renderers.current as string) pattern:"*GPU*"
```
