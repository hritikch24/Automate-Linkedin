// HTML Slideshow Generator for YouTube Facts
const fs = require('fs-extra');
const path = require('path');
const puppeteer = require('puppeteer');

/**
 * Generate an HTML slideshow for fact videos
 * @param {string} title - Video title
 * @param {Array} facts - Array of facts
 * @param {string} category - Category of facts
 * @param {string} outputDir - Directory to save files
 * @returns {Promise<string>} - Path to the generated HTML file
 */
async function generateHTMLSlideshow(title, facts, category, outputDir) {
  console.log(`Generating HTML slideshow for ${facts.length} ${category} facts...`);
  
  // Ensure output directory exists
  await fs.ensureDir(outputDir);
  
  // Create HTML content
  const htmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title}</title>
  <style>
    body, html {
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      font-family: 'Arial', sans-serif;
      overflow: hidden;
    }
    .slideshow-container {
      width: 100%;
      height: 100%;
      position: relative;
    }
    .slide {
      width: 100%;
      height: 100%;
      display: none;
      position: absolute;
      top: 0;
      left: 0;
      padding: 40px;
      box-sizing: border-box;
      text-align: center;
      justify-content: center;
      align-items: center;
      flex-direction: column;
      background-size: cover;
      background-position: center;
      color: white;
      text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
    }
    .slide-title {
      font-size: 64px;
      margin-bottom: 40px;
      font-weight: bold;
    }
    .slide-content {
      font-size: 48px;
      max-width: 80%;
      line-height: 1.4;
    }
    .slide.active {
      display: flex;
    }
    .slide-number {
      position: absolute;
      bottom: 20px;
      right: 20px;
      font-size: 24px;
      color: white;
      background-color: rgba(0, 0, 0, 0.5);
      padding: 5px 10px;
      border-radius: 5px;
    }
    
    /* Category-specific styles */
    .history { background-color: #8B4513; }
    .geography { background-color: #006400; }
    .science { background-color: #4B0082; }
    .ancient_civilizations { background-color: #800000; }
    .space { background-color: #191970; }
    .ocean { background-color: #00008B; }
  </style>
</head>
<body>
  <div class="slideshow-container">
    <!-- Title Slide -->
    <div class="slide ${category} active" id="slide-0">
      <div class="slide-title">${title}</div>
      <div class="slide-content">Amazing facts you never knew!</div>
      <div class="slide-number">1/${facts.length + 1}</div>
    </div>
    
    <!-- Fact Slides -->
    ${facts.map((fact, index) => {
      const factText = typeof fact === 'string' ? fact : (fact.text || 'Interesting fact');
      return `
    <div class="slide ${category}" id="slide-${index + 1}">
      <div class="slide-content">${factText}</div>
      <div class="slide-number">${index + 2}/${facts.length + 1}</div>
    </div>`;
    }).join('')}
  </div>

  <script>
    // Slideshow script
    let currentSlide = 0;
    const slides = document.querySelectorAll('.slide');
    const totalSlides = slides.length;
    
    function showSlide(n) {
      // Hide all slides
      slides.forEach(slide => slide.classList.remove('active'));
      
      // Show the current slide
      slides[n].classList.add('active');
      currentSlide = n;
    }
    
    function nextSlide() {
      if (currentSlide < totalSlides - 1) {
        showSlide(currentSlide + 1);
      } else {
        // Loop back to first slide
        showSlide(0);
      }
    }
    
    // Advance slides automatically every 5 seconds
    setInterval(nextSlide, 5000);
  </script>
</body>
</html>
  `;
  
  // Save HTML file
  const htmlFilePath = path.join(outputDir, `${category}_slideshow.html`);
  await fs.writeFile(htmlFilePath, htmlContent);
  
  console.log(`HTML slideshow generated at: ${htmlFilePath}`);
  return htmlFilePath;
}

/**
 * Capture slideshow as images using Puppeteer
 * @param {string} htmlFilePath - Path to the HTML slideshow
 * @param {number} slideCount - Number of slides (facts + title slide)
 * @param {string} outputDir - Directory to save images
 * @returns {Promise<Array<string>>} - Paths to the captured images
 */
async function captureSlideImages(htmlFilePath, slideCount, outputDir) {
  console.log(`Capturing ${slideCount} slides as images...`);
  
  const imageOutputDir = path.join(outputDir, 'slides');
  await fs.ensureDir(imageOutputDir);
  
  const imagePaths = [];
  
  try {
    // Launch headless browser
    const browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    
    // Set viewport to 1280x720 (720p)
    await page.setViewport({
      width: 1280,
      height: 720,
      deviceScaleFactor: 1
    });
    
    // Load the HTML file
    await page.goto(`file://${htmlFilePath}`, {
      waitUntil: 'networkidle0'
    });
    
    // Capture each slide
    for (let i = 0; i < slideCount; i++) {
      // Show the current slide
      await page.evaluate((slideIndex) => {
        const slides = document.querySelectorAll('.slide');
        slides.forEach(slide => slide.classList.remove('active'));
        slides[slideIndex].classList.add('active');
      }, i);
      
      // Wait for any animations to complete
      await page.waitForTimeout(500);
      
      // Capture screenshot
      const imagePath = path.join(imageOutputDir, `slide_${i}.png`);
      await page.screenshot({
        path: imagePath,
        type: 'png',
        quality: 100
      });
      
      imagePaths.push(imagePath);
      console.log(`Captured slide ${i + 1}/${slideCount}`);
    }
    
    // Close browser
    await browser.close();
    
    console.log(`All slides captured successfully!`);
    return imagePaths;
  } catch (error) {
    console.error('Error capturing slide images:', error.message);
    throw error;
  }
}

/**
 * Create slideshow video from images using FFmpeg
 * @param {Array<string>} imagePaths - Paths to the slide images
 * @param {string} outputVideoPath - Path for the output video
 * @returns {Promise<string>} - Path to the created video
 */
async function createSlideshowVideo(imagePaths, outputVideoPath) {
  console.log(`Creating slideshow video from ${imagePaths.length} images...`);
  
  try {
    // Create a temporary file that lists all the images
    const listFilePath = path.join(path.dirname(outputVideoPath), 'slides_list.txt');
    const listContent = imagePaths.map(imagePath => {
      // Each image shows for 5 seconds
      return `file '${imagePath}'\nduration 5`;
    }).join('\n');
    
    // Add the last image with a duration (required by FFmpeg concat)
    const lastImage = imagePaths[imagePaths.length - 1];
    const finalListContent = `${listContent}\nfile '${lastImage}'\nduration 1`;
    
    await fs.writeFile(listFilePath, finalListContent);
    
    // Use FFmpeg to create video from images
    const { spawn } = require('child_process');
    const ffmpegPath = require('@ffmpeg-installer/ffmpeg').path;
    
    // Build FFmpeg command
    const args = [
      '-f', 'concat',
      '-safe', '0',
      '-i', listFilePath,
      '-vsync', 'vfr',
      '-pix_fmt', 'yuv420p',
      '-c:v', 'libx264',
      '-r', '30',  // 30fps
      '-y',  // Overwrite output file if it exists
      outputVideoPath
    ];
    
    // Execute FFmpeg
    await new Promise((resolve, reject) => {
      console.log(`Executing FFmpeg command: ${ffmpegPath} ${args.join(' ')}`);
      
      const process = spawn(ffmpegPath, args);
      
      process.stdout.on('data', (data) => {
        console.log(`FFmpeg stdout: ${data}`);
      });
      
      process.stderr.on('data', (data) => {
        console.log(`FFmpeg stderr: ${data}`);
      });
      
      process.on('close', (code) => {
        if (code === 0) {
          console.log(`FFmpeg process completed successfully`);
          resolve();
        } else {
          console.error(`FFmpeg process exited with code ${code}`);
          reject(new Error(`FFmpeg process exited with code ${code}`));
        }
      });
    });
    
    console.log(`Video created successfully: ${outputVideoPath}`);
    return outputVideoPath;
  } catch (error) {
    console.error('Error creating slideshow video:', error.message);
    throw error;
  }
}

/**
 * Generate a video from facts using HTML slideshow
 * @param {string} title - Video title
 * @param {Array} facts - Array of facts
 * @param {string} category - Category of facts
 * @param {string} outputVideoPath - Path for the output video
 * @returns {Promise<string>} - Path to the created video
 */
async function generateFactVideo(title, facts, category, outputVideoPath) {
  try {
    const outputDir = path.dirname(outputVideoPath);
    
    // Generate HTML slideshow
    const htmlFilePath = await generateHTMLSlideshow(
      title,
      facts,
      category,
      outputDir
    );
    
    // Capture slides as images
    const slideCount = facts.length + 1; // facts + title slide
    const imagePaths = await captureSlideImages(
      htmlFilePath,
      slideCount,
      outputDir
    );
    
    // Create video from images
    const videoPath = await createSlideshowVideo(
      imagePaths,
      outputVideoPath
    );
    
    return videoPath;
  } catch (error) {
    console.error('Error generating fact video:', error.message);
    throw error;
  }
}

module.exports = {
  generateHTMLSlideshow,
  captureSlideImages,
  createSlideshowVideo,
  generateFactVideo
};