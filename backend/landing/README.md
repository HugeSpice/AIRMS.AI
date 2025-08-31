# Hyperspeed Effect

A stunning 3D animated highway effect built with React, Three.js, and post-processing effects. Create immersive, high-speed travel visualizations with customizable distortions, colors, and animations.

![Hyperspeed Effect Demo](https://via.placeholder.com/800x400/000000/00f5ff?text=Hyperspeed+Effect)

## ✨ Features

- 🚗 **Dynamic Car Lights**: Animated car headlights and taillights moving along highway lanes
- 🛣️ **Realistic Highway**: Multi-lane roads with proper lane markings and shoulder lines
- 🌊 **Multiple Distortions**: Six different distortion effects (turbulent, mountain, XY, long race, deep)
- 🎨 **Customizable Colors**: Full control over road, car, and lighting colors
- 📱 **Touch & Mouse Support**: Interactive speed control via click/hold or touch
- 🎯 **Performance Optimized**: Efficient rendering with instanced geometry and post-processing
- 🎭 **Multiple Presets**: Six pre-configured visual styles to choose from
- 📱 **Responsive Design**: Works seamlessly on desktop and mobile devices

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd hyperspeed-effect

# Install dependencies
npm install

# Start development server
npm run dev
```

### Basic Usage

```tsx
import Hyperspeed from './src/Hyperspeed';

function App() {
  return (
    <div style={{ width: '100vw', height: '100vh' }}>
      <Hyperspeed />
    </div>
  );
}
```

### With Custom Options

```tsx
import Hyperspeed from './src/Hyperspeed';

function App() {
  return (
    <div style={{ width: '100vw', height: '100vh' }}>
      <Hyperspeed
        effectOptions={{
          distortion: 'turbulentDistortion',
          speedUp: 3,
          fov: 90,
          fovSpeedUp: 150,
          colors: {
            roadColor: 0x080808,
            leftCars: [0xD856BF, 0x6750A2, 0xC247AC],
            rightCars: [0x03B3C3, 0x0E5EA5, 0x324555],
            sticks: 0x03B3C3,
          },
          onSpeedUp: (event) => console.log('Speeding up!'),
          onSlowDown: (event) => console.log('Slowing down!'),
        }}
      />
    </div>
  );
}
```

### Using Presets

```tsx
import Hyperspeed from './src/Hyperspeed';
import { hyperspeedPresets } from './src/presets';

function App() {
  return (
    <div style={{ width: '100vw', height: '100vh' }}>
      <Hyperspeed effectOptions={hyperspeedPresets.two} />
    </div>
  );
}
```

## 🎛️ Configuration Options

### Core Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `distortion` | `string \| Distortion` | `'turbulentDistortion'` | Distortion effect type |
| `length` | `number` | `400` | Length of the highway |
| `roadWidth` | `number` | `10` | Width of each road section |
| `islandWidth` | `number` | `2` | Width of the center divider |
| `lanesPerRoad` | `number` | `4` | Number of lanes per road direction |

### Camera & Animation

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `fov` | `number` | `90` | Field of view (normal state) |
| `fovSpeedUp` | `number` | `150` | Field of view (speed up state) |
| `speedUp` | `number` | `2` | Speed multiplier when active |
| `carLightsFade` | `number` | `0.4` | Car lights fade intensity |

### Visual Elements

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `totalSideLightSticks` | `number` | `20` | Number of side light posts |
| `lightPairsPerRoadWay` | `number` | `40` | Car light pairs per direction |
| `shoulderLinesWidthPercentage` | `number` | `0.05` | Width of shoulder lines |
| `brokenLinesWidthPercentage` | `number` | `0.1` | Width of broken lines |
| `brokenLinesLengthPercentage` | `number` | `0.5` | Length of broken line segments |

### Car Properties

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `carLightsLength` | `[number, number]` | `[12, 80]` | Min/max car light length |
| `carLightsRadius` | `[number, number]` | `[0.05, 0.14]` | Min/max car light radius |
| `carWidthPercentage` | `[number, number]` | `[0.3, 0.5]` | Min/max car width percentage |
| `movingAwaySpeed` | `[number, number]` | `[60, 80]` | Speed range for receding cars |
| `movingCloserSpeed` | `[number, number]` | `[-120, -160]` | Speed range for approaching cars |

### Colors

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `colors.roadColor` | `number` | `0x080808` | Road surface color |
| `colors.islandColor` | `number` | `0x0a0a0a` | Center divider color |
| `colors.background` | `number` | `0x000000` | Background/fog color |
| `colors.shoulderLines` | `number` | `0xffffff` | Shoulder line color |
| `colors.brokenLines` | `number` | `0xffffff` | Broken line color |
| `colors.leftCars` | `number[]` | `[0xd856bf, 0x6750a2, 0xc247ac]` | Left car light colors |
| `colors.rightCars` | `number[]` | `[0x03b3c3, 0x0e5ea5, 0x324555]` | Right car light colors |
| `colors.sticks` | `number` | `0x03b3c3` | Side light post color |

### Event Handlers

| Option | Type | Description |
|--------|------|-------------|
| `onSpeedUp` | `(event: MouseEvent \| TouchEvent) => void` | Callback when speed up starts |
| `onSlowDown` | `(event: MouseEvent \| TouchEvent) => void` | Callback when speed up ends |

## 🎨 Available Presets

The component includes six pre-configured presets:

1. **Preset One** - Default turbulent distortion with purple/cyan colors
2. **Preset Two** - Mountain distortion with red/purple theme
3. **Preset Three** - XY distortion with red/yellow theme and faster speed
4. **Preset Four** - Long race distortion with pink/cyan theme
5. **Preset Five** - Turbulent distortion with orange/blue theme
6. **Preset Six** - Deep distortion with red/cream theme and wider roads

## 🛠️ Available Distortions

- `turbulentDistortion` - Dynamic turbulent movement (default)
- `mountainDistortion` - Gentle mountain-like curves
- `xyDistortion` - Side-to-side and up-down movement
- `LongRaceDistortion` - Racing-style curves
- `deepDistortion` - Deep perspective distortion
- `turbulentDistortionStill` - Static turbulent effect
- `deepDistortionStill` - Static deep effect

## 🎮 Controls

- **Mouse**: Click and hold to speed up
- **Touch**: Tap and hold to speed up
- **Keyboard**: Focus the element and use spacebar (when accessible)

## 📱 Browser Support

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

Requires WebGL support for 3D rendering.

## 🏗️ Architecture

The component is built with:

- **React 18** for component lifecycle and hooks
- **Three.js** for 3D rendering and scene management
- **postprocessing** for bloom and anti-aliasing effects
- **TypeScript** for type safety
- **Vite** for fast development and building

### Key Classes

- `App` - Main application and scene manager
- `Road` - Highway geometry and lane markings
- `CarLights` - Car headlight and taillight animations
- `LightsSticks` - Side lighting posts
- `Distortions` - Mathematical distortion effects

## 🎯 Performance Tips

1. **Reduce particle counts** for lower-end devices:
   ```tsx
   effectOptions={{
     lightPairsPerRoadWay: 20, // Reduce from default 40
     totalSideLightSticks: 10, // Reduce from default 20
   }}
   ```

2. **Simplify distortions** for better performance:
   ```tsx
   effectOptions={{
     distortion: 'turbulentDistortionStill', // Use static version
   }}
   ```

3. **Adjust render distance**:
   ```tsx
   effectOptions={{
     length: 200, // Reduce from default 400
   }}
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by retro synthwave and cyberpunk aesthetics
- Built with the amazing Three.js library
- Post-processing effects powered by pmndrs/postprocessing

## 🐛 Troubleshooting

### Common Issues

**Component not rendering:**
- Ensure container has explicit width/height
- Check browser WebGL support
- Verify all dependencies are installed

**Performance issues:**
- Reduce particle counts in options
- Use static distortion effects
- Lower the render resolution

**Touch events not working:**
- Ensure CSS `touch-action` is properly set
- Check for conflicting event handlers
- Verify passive event listener support

**Memory leaks:**
- Component automatically cleans up on unmount
- Avoid creating multiple instances simultaneously
- Check browser developer tools for WebGL context limits

---

Made with ❤️ and lots of ☕
