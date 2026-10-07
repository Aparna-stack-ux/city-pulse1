import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js';

const markerColorForPoint = (point) => {
    if (point.status_code === 'resolved') return 0x39d98a;
    if (point.category_code === 'emergency' || ['high', 'urgent'].includes(point.priority_code)) return 0xff526b;
    if (['pending', 'assigned', 'in_progress'].includes(point.status_code)) return 0xffb547;
    if (point.is_hotspot) return 0x54d7ff;
    return 0x4b9fff;
};

const addPreviewDistrict = (scene) => {
    const ground = new THREE.Mesh(
        new THREE.PlaneGeometry(27, 19),
        new THREE.MeshStandardMaterial({
            color: 0x09233d,
            metalness: 0.3,
            roughness: 0.72,
            transparent: true,
            opacity: 0.68,
        })
    );
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.1;
    scene.add(ground);

    const roadMaterial = new THREE.MeshStandardMaterial({
        color: 0x07182a,
        emissive: 0x083d60,
        emissiveIntensity: 0.35,
        roughness: 0.48,
    });
    const roads = [[27, 1.1, 0, 0], [1.1, 19, 0, 0], [27, 0.65, 0, -6.5]];
    roads.forEach(([width, depth, x, z]) => {
        const road = new THREE.Mesh(new THREE.PlaneGeometry(width, depth), roadMaterial);
        road.rotation.x = -Math.PI / 2;
        road.position.set(x, 0, z);
        scene.add(road);
    });

    const grid = new THREE.GridHelper(27, 18, 0x29a9dc, 0x174b70);
    grid.position.y = -0.06;
    grid.material.transparent = true;
    grid.material.opacity = 0.18;
    scene.add(grid);

    const buildingGeometry = new THREE.BoxGeometry(1.15, 1, 1.1);
    const buildingMaterial = new THREE.MeshStandardMaterial({
        color: 0x1f8fba,
        emissive: 0x0b4770,
        emissiveIntensity: 0.45,
        metalness: 0.38,
        roughness: 0.37,
    });
    const blocks = [];
    for (let x = -11; x <= 11; x += 3.1) {
        for (let z = -7.5; z <= 7.5; z += 3.2) {
            if (Math.abs(x) < 2 && Math.abs(z) < 2) continue;
            if ((Math.round(x * 3 + z * 2) % 7) === 0) continue;
            const height = 1.2 + (Math.abs(Math.round(x * 3 + z * 5)) % 5) * 0.52;
            const building = new THREE.Mesh(buildingGeometry, buildingMaterial);
            building.scale.y = height;
            building.position.set(x, height / 2, z);
            scene.add(building);
            blocks.push(building);
        }
    }

    const treeTrunk = new THREE.CylinderGeometry(0.055, 0.08, 0.55, 6);
    const treeCrown = new THREE.ConeGeometry(0.3, 0.72, 7);
    const trunkMaterial = new THREE.MeshStandardMaterial({ color: 0x755637, roughness: 0.85 });
    const crownMaterial = new THREE.MeshStandardMaterial({ color: 0x24a887, emissive: 0x075c50, emissiveIntensity: 0.34, roughness: 0.62 });
    [-12, -5, 6, 12].forEach((x, index) => {
        const z = index % 2 ? 5.2 : -5.4;
        const trunk = new THREE.Mesh(treeTrunk, trunkMaterial);
        trunk.position.set(x, 0.28, z);
        scene.add(trunk);
        const crown = new THREE.Mesh(treeCrown, crownMaterial);
        crown.position.set(x, 0.88, z);
        scene.add(crown);
    });

    return blocks;
};

const mountMapPreview = (container) => {
    const pointSource = document.getElementById(container.dataset.pointsId || 'map-data');
    const points = pointSource ? JSON.parse(pointSource.textContent || '[]') : [];
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(37, 1, 0.1, 80);
    camera.position.set(0, 18, 24);
    camera.lookAt(0, 2.5, 0);
    scene.add(new THREE.HemisphereLight(0xa9e6ff, 0x071525, 2));
    const keyLight = new THREE.DirectionalLight(0xe5f8ff, 2.2);
    keyLight.position.set(-8, 18, 12);
    scene.add(keyLight);
    const accentLight = new THREE.PointLight(0x28c7ff, 25, 28, 2);
    accentLight.position.set(2, 7, 0);
    scene.add(accentLight);
    const district = new THREE.Group();
    scene.add(district);
    const blocks = addPreviewDistrict(district);
    const markerMeshes = [];
    const markerRings = [];
    const markerRaycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    const markerStem = new THREE.CylinderGeometry(0.07, 0.13, 0.58, 10);
    const markerHead = new THREE.SphereGeometry(0.23, 14, 12);
    const markerBase = new THREE.TorusGeometry(0.3, 0.035, 6, 24);

    points.forEach((point, index) => {
        const longitude = Number(point.lng);
        const latitude = Number(point.lat);
        if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) return;

        const markerColor = markerColorForPoint(point);
        const markerMaterial = new THREE.MeshStandardMaterial({
            color: markerColor,
            emissive: markerColor,
            emissiveIntensity: 0.42,
            metalness: 0.24,
            roughness: 0.3,
        });
        const marker = new THREE.Group();
        marker.position.set((longitude - 82.5) * 0.72, 0.12, (22 - latitude) * 0.44);
        marker.userData.pointIndex = index;

        const stem = new THREE.Mesh(markerStem, markerMaterial);
        stem.position.y = 0.34;
        stem.userData.pointIndex = index;
        marker.add(stem);

        const head = new THREE.Mesh(markerHead, markerMaterial);
        head.position.y = 0.72;
        head.userData.pointIndex = index;
        marker.add(head);

        const ring = new THREE.Mesh(
            markerBase,
            new THREE.MeshBasicMaterial({ color: markerColor, transparent: true, opacity: 0.72 })
        );
        ring.rotation.x = Math.PI / 2;
        ring.position.y = 0.08;
        ring.userData.pointIndex = index;
        marker.add(ring);
        markerRings.push(ring);
        markerMeshes.push(stem, head, ring);
        district.add(marker);
    });

    let renderer;
    try {
        renderer = new THREE.WebGLRenderer({
            alpha: true,
            antialias: window.innerWidth >= 768,
            powerPreference: 'low-power',
        });
    } catch (error) {
        container.classList.add('is-fallback');
        return;
    }
    renderer.setClearColor(0x000000, 0);
    renderer.domElement.setAttribute('aria-hidden', 'true');
    container.prepend(renderer.domElement);
    container.classList.add('is-ready');

    const resize = () => {
        const width = Math.max(container.clientWidth, 1);
        const height = Math.max(container.clientHeight, 1);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, width < 600 ? 1 : 1.25));
        renderer.setSize(width, height, false);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.render(scene, camera);
    };
    resize();

    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let dragStart = null;
    let dragged = false;
    let rotationY = 0;
    const raycast = (event) => {
        if (dragged) {
            dragged = false;
            return;
        }
        const rect = renderer.domElement.getBoundingClientRect();
        pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        markerRaycaster.setFromCamera(pointer, camera);
        const selected = markerRaycaster.intersectObjects(markerMeshes, false)[0]?.object;
        if (selected) {
            container.dispatchEvent(new CustomEvent('citypulse:3d-map-marker', {
                bubbles: true,
                detail: { index: selected.userData.pointIndex },
            }));
        }
    };

    renderer.domElement.addEventListener('pointerdown', (event) => {
        if (event.button !== 0) return;
        dragStart = { x: event.clientX, y: event.clientY };
        dragged = false;
        renderer.domElement.setPointerCapture(event.pointerId);
    });
    renderer.domElement.addEventListener('pointerup', (event) => {
        if (dragStart && !dragged) raycast(event);
        dragStart = null;
    });
    renderer.domElement.addEventListener('pointercancel', () => {
        dragStart = null;
    });
    renderer.domElement.addEventListener('pointermove', (event) => {
        if (dragStart) {
            const deltaX = event.clientX - dragStart.x;
            const deltaY = event.clientY - dragStart.y;
            if (Math.abs(deltaX) + Math.abs(deltaY) > 4) dragged = true;
            if (dragged) {
                rotationY += deltaX * 0.008;
                camera.position.y = Math.max(10, Math.min(28, camera.position.y - deltaY * 0.025));
                dragStart = { x: event.clientX, y: event.clientY };
                if (reducedMotion) renderer.render(scene, camera);
            }
        }
        const rect = renderer.domElement.getBoundingClientRect();
        pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        markerRaycaster.setFromCamera(pointer, camera);
        renderer.domElement.style.cursor = markerRaycaster.intersectObjects(markerMeshes, false).length ? 'pointer' : 'grab';
    });
    renderer.domElement.addEventListener('wheel', (event) => {
        event.preventDefault();
        camera.position.z = Math.max(14, Math.min(38, camera.position.z + Math.sign(event.deltaY) * 1.5));
        if (reducedMotion) renderer.render(scene, camera);
    }, { passive: false });

    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(container);
    window.addEventListener('resize', resize, { passive: true });

    if (reducedMotion) return;

    let frameId;
    let previousFrame = 0;
    const animate = (time) => {
        frameId = window.requestAnimationFrame(animate);
        if (document.hidden || time - previousFrame < 1000 / 24) return;
        previousFrame = time;
        district.rotation.y = rotationY + Math.sin(time * 0.0001) * 0.035;
        markerRings.forEach((ring, index) => {
            const phase = time * 0.0017 + index;
            ring.scale.setScalar(1 + (Math.sin(phase) + 1) * 0.1);
        });
        camera.position.x += (pointer.x * 0.7 - camera.position.x) * 0.008;
        camera.lookAt(pointer.x * 0.35, 2.5, pointer.y * 0.3);
        renderer.render(scene, camera);
    };
    frameId = window.requestAnimationFrame(animate);
    window.addEventListener('pagehide', () => {
        window.cancelAnimationFrame(frameId);
        resizeObserver.disconnect();
        renderer.dispose();
    }, { once: true });
};

const mount = () => {
    if (!document.body || document.getElementById('citypulse-three-scene')) return;

    const mapPreviews = document.querySelectorAll('[data-citypulse-3d="map"]');
    if (mapPreviews.length) {
        mapPreviews.forEach(mountMapPreview);
        return;
    }

    const host = document.createElement('div');
    host.id = 'citypulse-three-scene';
    host.setAttribute('aria-hidden', 'true');
    const canvas = document.createElement('canvas');
    host.append(canvas);
    document.body.prepend(host);

    let renderer;
    try {
        renderer = new THREE.WebGLRenderer({
            alpha: true,
            antialias: window.innerWidth >= 768,
            canvas,
            powerPreference: 'low-power',
        });
    } catch (error) {
        host.remove();
        return;
    }

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(36, 1, 0.1, 120);
    camera.position.set(0, 25, 43);
    camera.lookAt(0, 3.5, 0);

    scene.add(new THREE.AmbientLight(0x9dcfff, 1.25));

    const keyLight = new THREE.DirectionalLight(0xd6efff, 2.1);
    keyLight.position.set(-14, 24, 18);
    scene.add(keyLight);

    const cyanLight = new THREE.PointLight(0x23bfff, 42, 42, 2);
    cyanLight.position.set(9, 8, 2);
    scene.add(cyanLight);

    const city = new THREE.Group();
    scene.add(city);

    const ground = new THREE.Mesh(
        new THREE.PlaneGeometry(38, 34),
        new THREE.MeshStandardMaterial({
            color: 0x09203a,
            metalness: 0.35,
            roughness: 0.72,
            transparent: true,
            opacity: 0.38,
        })
    );
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.12;
    city.add(ground);

    const grid = new THREE.GridHelper(38, 24, 0x35bfff, 0x1b5b86);
    grid.position.y = -0.08;
    grid.material.transparent = true;
    grid.material.opacity = 0.22;
    city.add(grid);

    const roadMaterial = new THREE.MeshStandardMaterial({
        color: 0x071629,
        emissive: 0x06304f,
        emissiveIntensity: 0.35,
        metalness: 0.3,
        roughness: 0.52,
        transparent: true,
        opacity: 0.72,
    });

    const addRoad = (width, height, x, z) => {
        const road = new THREE.Mesh(new THREE.PlaneGeometry(width, height), roadMaterial);
        road.rotation.x = -Math.PI / 2;
        road.position.set(x, 0, z);
        city.add(road);
    };

    addRoad(38, 2.1, 0, 0);
    addRoad(2, 34, 0, 0);
    addRoad(38, 1.1, 0, -10.5);

    const buildingColors = [0x12619b, 0x117f9b, 0x174a80, 0x167f83, 0x23548c];
    const gridPositions = [-14, -9, -4, 4, 9, 14];

    gridPositions.forEach((x, column) => {
        gridPositions.forEach((z, row) => {
            if ((column === 2 || column === 3) && (row === 2 || row === 3)) return;
            if ((column * 3 + row * 5) % 11 === 0) return;

            const width = 2.15 + ((column + row) % 2) * 0.42;
            const depth = 2.1 + ((column * 2 + row) % 3) * 0.18;
            const height = 2.2 + ((column * 7 + row * 4) % 8) * 0.72;
            const material = new THREE.MeshStandardMaterial({
                color: buildingColors[(column + row * 2) % buildingColors.length],
                emissive: 0x0a4b73,
                emissiveIntensity: 0.12,
                metalness: 0.46,
                roughness: 0.34,
                transparent: true,
                opacity: 0.92,
            });

            const geometry = new THREE.BoxGeometry(width, height, depth);
            const building = new THREE.Mesh(geometry, material);
            building.position.set(x, height / 2, z);
            city.add(building);

            const edges = new THREE.LineSegments(
                new THREE.EdgesGeometry(geometry),
                new THREE.LineBasicMaterial({ color: 0x7bdfff, transparent: true, opacity: 0.22 })
            );
            edges.position.copy(building.position);
            city.add(edges);

            const roofLight = new THREE.Mesh(
                new THREE.BoxGeometry(width * 0.58, 0.035, 0.055),
                new THREE.MeshBasicMaterial({ color: column % 2 ? 0x4fe5d2 : 0x42bbff })
            );
            roofLight.position.set(x, height + 0.025, z);
            city.add(roofLight);
        });
    });

    const trunkGeometry = new THREE.CylinderGeometry(0.09, 0.13, 0.72, 7);
    const crownGeometry = new THREE.ConeGeometry(0.46, 1.25, 8);
    const trunkMaterial = new THREE.MeshStandardMaterial({ color: 0x75583d, roughness: 0.86 });
    const crownMaterial = new THREE.MeshStandardMaterial({ color: 0x218e78, emissive: 0x07594f, emissiveIntensity: 0.2, roughness: 0.68 });
    [-17, -12, -7, 7, 12, 17].forEach((x, index) => {
        const z = index % 2 === 0 ? -4.1 : 4.1;
        const trunk = new THREE.Mesh(trunkGeometry, trunkMaterial);
        trunk.position.set(x, 0.36, z);
        city.add(trunk);
        const crown = new THREE.Mesh(crownGeometry, crownMaterial);
        crown.position.set(x, 1.26, z);
        city.add(crown);
    });

    const lampPoleGeometry = new THREE.CylinderGeometry(0.045, 0.075, 2.7, 8);
    const lampArmGeometry = new THREE.BoxGeometry(0.52, 0.06, 0.06);
    const lampMaterial = new THREE.MeshStandardMaterial({ color: 0x678ba6, metalness: 0.78, roughness: 0.28 });
    const lampGlowMaterial = new THREE.MeshBasicMaterial({ color: 0x74e6ff });
    [-15, -5, 5, 15].forEach((x, index) => {
        const z = index % 2 ? -1.55 : 1.55;
        const pole = new THREE.Mesh(lampPoleGeometry, lampMaterial);
        pole.position.set(x, 1.35, z);
        city.add(pole);
        const arm = new THREE.Mesh(lampArmGeometry, lampMaterial);
        arm.position.set(x + (index % 2 ? -0.22 : 0.22), 2.66, z);
        city.add(arm);
        const lamp = new THREE.Mesh(new THREE.SphereGeometry(0.11, 10, 8), lampGlowMaterial);
        lamp.position.set(x + (index % 2 ? -0.44 : 0.44), 2.58, z);
        city.add(lamp);
    });

    const sensorMaterial = new THREE.MeshStandardMaterial({
        color: 0x80f1ff,
        emissive: 0x13b8ff,
        emissiveIntensity: 1.35,
        metalness: 0.35,
        roughness: 0.22,
    });
    const sensors = [];
    [[-9, 8.8, -9], [9, 9.6, 9], [14, 7.4, -4]].forEach(([x, y, z]) => {
        const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.06, 0.9, 7), lampMaterial);
        mast.position.set(x, y, z);
        city.add(mast);
        const sensor = new THREE.Mesh(new THREE.OctahedronGeometry(0.27, 0), sensorMaterial);
        sensor.position.set(x, y + 0.55, z);
        sensor.userData.floatOffset = x * 0.2 + z * 0.13;
        city.add(sensor);
        sensors.push(sensor);
    });

    const route = new THREE.CatmullRomCurve3([
        new THREE.Vector3(-16, 0.16, 0),
        new THREE.Vector3(-11, 0.16, 0),
        new THREE.Vector3(-5, 0.16, 0),
        new THREE.Vector3(0, 0.16, 0),
        new THREE.Vector3(4, 0.16, 0),
        new THREE.Vector3(10, 0.16, 0),
        new THREE.Vector3(16, 0.16, 0),
    ]);

    city.add(new THREE.Mesh(
        new THREE.TubeGeometry(route, 90, 0.055, 6, false),
        new THREE.MeshBasicMaterial({ color: 0x35c6ff, transparent: true, opacity: 0.64 })
    ));

    const vehicleMaterial = new THREE.MeshStandardMaterial({ color: 0x38c5f4, emissive: 0x0879b5, emissiveIntensity: 0.65, metalness: 0.48, roughness: 0.28 });
    const vehicleCabMaterial = new THREE.MeshStandardMaterial({ color: 0x9feaff, metalness: 0.38, roughness: 0.22 });
    const wheelGeometry = new THREE.CylinderGeometry(0.13, 0.13, 0.12, 10);
    const wheelMaterial = new THREE.MeshStandardMaterial({ color: 0x101b27, roughness: 0.88 });
    const vehicles = [0.08, 0.43, 0.76].map((offset, index) => {
        const vehicle = new THREE.Group();
        const body = new THREE.Mesh(new THREE.BoxGeometry(0.92, 0.32, 0.5), index === 1 ? new THREE.MeshStandardMaterial({ color: 0xf8b84a, emissive: 0x9d4c08, emissiveIntensity: 0.5, metalness: 0.42, roughness: 0.3 }) : vehicleMaterial);
        body.position.y = 0.25;
        vehicle.add(body);
        const cabin = new THREE.Mesh(new THREE.BoxGeometry(0.46, 0.24, 0.43), vehicleCabMaterial);
        cabin.position.set(-0.06, 0.51, 0);
        vehicle.add(cabin);
        [-0.3, 0.3].forEach((x) => [-0.27, 0.27].forEach((z) => {
            const wheel = new THREE.Mesh(wheelGeometry, wheelMaterial);
            wheel.rotation.x = Math.PI / 2;
            wheel.position.set(x, 0.13, z);
            vehicle.add(wheel);
        }));
        vehicle.userData.routeOffset = offset;
        vehicle.userData.routeSpeed = index === 1 ? -1 : 1;
        vehicle.position.copy(route.getPointAt(offset));
        city.add(vehicle);
        return vehicle;
    });

    const pulses = [0, 0.34, 0.68].map((offset) => {
        const pulse = new THREE.Mesh(
            new THREE.SphereGeometry(0.16, 12, 10),
            new THREE.MeshBasicMaterial({ color: 0x90f5ff })
        );
        city.add(pulse);
        pulse.userData.offset = offset;
        return pulse;
    });

    const orbit = new THREE.Mesh(
        new THREE.TorusGeometry(2.15, 0.025, 5, 80),
        new THREE.MeshBasicMaterial({ color: 0x3dceff, transparent: true, opacity: 0.36 })
    );
    orbit.rotation.x = Math.PI / 2;
    orbit.position.set(0, 7.1, -3);
    city.add(orbit);

    const pointerTarget = new THREE.Vector2();
    window.addEventListener('pointermove', (event) => {
        pointerTarget.x = (event.clientX / Math.max(window.innerWidth, 1) - 0.5) * 2;
        pointerTarget.y = (event.clientY / Math.max(window.innerHeight, 1) - 0.5) * 2;
    }, { passive: true });

    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const setSize = () => {
        const width = window.innerWidth;
        const height = window.innerHeight;
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, width < 768 ? 1 : 1.35));
        renderer.setSize(width, height, false);
        camera.aspect = width / height;
        camera.position.z = width < 768 ? 50 : 43;
        camera.updateProjectionMatrix();
        city.scale.setScalar(width < 768 ? 0.82 : 1);
        renderer.render(scene, camera);
    };

    setSize();
    window.addEventListener('resize', setSize, { passive: true });
    const resizeObserver = new ResizeObserver(setSize);
    resizeObserver.observe(host);

    if (reducedMotion) return;

    let frameId;
    let lastFrameTime = 0;
    const animate = (time) => {
        if (document.hidden) {
            frameId = window.requestAnimationFrame(animate);
            return;
        }
        if (time - lastFrameTime < 1000 / 30) {
            frameId = window.requestAnimationFrame(animate);
            return;
        }
        lastFrameTime = time;
        city.rotation.y = Math.sin(time * 0.00012) * 0.025;
        sensors.forEach((sensor) => {
            sensor.position.y += Math.sin(time * 0.001 + sensor.userData.floatOffset) * 0.0008;
        });
        vehicles.forEach((vehicle) => {
            const progress = ((time * 0.000018 * vehicle.userData.routeSpeed + vehicle.userData.routeOffset) % 1 + 1) % 1;
            const position = route.getPointAt(progress);
            const tangent = route.getTangentAt(progress);
            vehicle.position.copy(position);
            vehicle.position.y = 0.08;
            vehicle.rotation.y = Math.atan2(tangent.x, tangent.z);
        });
        camera.position.x += (pointerTarget.x * 1.1 - camera.position.x) * 0.006;
        camera.lookAt(pointerTarget.x * 0.24, 3.5 + pointerTarget.y * 0.18, 0);
        pulses.forEach((pulse) => {
            const progress = (time * 0.000035 + pulse.userData.offset) % 1;
            pulse.position.copy(route.getPointAt(progress));
        });
        renderer.render(scene, camera);
        frameId = window.requestAnimationFrame(animate);
    };

    frameId = window.requestAnimationFrame(animate);
    window.addEventListener('pagehide', () => {
        window.cancelAnimationFrame(frameId);
        resizeObserver.disconnect();
        renderer.dispose();
    }, { once: true });
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount, { once: true });
} else {
    mount();
}