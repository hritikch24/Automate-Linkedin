/**
 * Ultra-basic image-based solution for facts videos
 * This uses the simplest possible approach to ensure it works in all environments
 */

const fs = require('fs-extra');
const { execSync } = require('child_process');
const path = require('path');

/**
 * Create an extremely basic image with text
 */
async function createBasicTextImage(text, imagePath) {
  console.log('Creating basic text image...');
  
  try {
    // Try the simplest possible convert command
    const command = `convert -size 1280x720 xc:blue -pointsize 30 -fill white -gravity center -annotate +0+0 "${text}" "${imagePath}"`;
    execSync(command, { stdio: 'inherit' });
    console.log(`Created text image at ${imagePath}`);
    return true;
  } catch (error) {
    console.error('Error creating text image:', error.message);
    
    // Fallback to even simpler image - just a blue background
    try {
      console.log('Falling back to simple blue background...');
      const fallbackCommand = `convert -size 1280x720 xc:blue "${imagePath}"`;
      execSync(fallbackCommand, { stdio: 'inherit' });
      console.log(`Created simple blue background at ${imagePath}`);
      return true;
    } catch (fallbackError) {
      console.error('Error creating simple background:', fallbackError.message);
      return false;
    }
  }
}

/**
 * Create a facts video using the simplest possible method
 */
async function createFactsImageVideo(facts, category, outputPath) {
  console.log('Creating ultra-simple facts video...');
  
  try {
    // Ensure the output directory exists
    const outputDir = path.dirname(outputPath);
    await fs.ensureDir(outputDir);
    
    // Create temp directory
    const tempDir = path.join(outputDir, 'temp');
    await fs.ensureDir(tempDir);
    
    // Ensure facts is never empty
    const validFacts = (facts && facts.length > 0) ? facts : [
      { text: "The human brain can process images in as little as 13 milliseconds." },
      { text: "The Earth is not a perfect sphere; it's an oblate spheroid, flattened at the poles." },
      { text: "There are more possible iterations of a game of chess than there are atoms in the universe." },
      { text: "Honey never spoils. Archaeologists have found pots of honey from ancient Egyptian tombs that are over 3,000 years old." },
      { text: "The longest recorded flight of a chicken is 13 seconds." }
    ];
    
    // Format title
    const title = `${validFacts.length} Amazing ${category.charAt(0).toUpperCase() + category.slice(1)} Facts`;
    
    // Format a very simple text for the image
    const simpleText = title;
    
    // Create image file path
    const imagePath = path.join(tempDir, 'facts_image.png');
    
    // Create a simple image
    const imageCreated = await createBasicTextImage(simpleText, imagePath);
    
    // Create video from image (or blue background if image creation failed)
    console.log('Converting to video...');
    
    if (imageCreated) {
      // Create video from image
      const ffmpegCommand = `ffmpeg -loop 1 -i "${imagePath}" -c:v libx264 -t 30 -pix_fmt yuv420p -y "${outputPath}"`;
      execSync(ffmpegCommand, { stdio: 'inherit' });
    } else {
      // Create a basic blue video
      const fallbackCommand = `ffmpeg -f lavfi -i color=c=blue:s=1280x720:d=30 -c:v libx264 -pix_fmt yuv420p -y "${outputPath}"`;
      execSync(fallbackCommand, { stdio: 'inherit' });
    }
    
    console.log(`Video created at ${outputPath}`);
    
    // Save description to file
    const descriptionFile = `${outputPath}.description.txt`;
    const descriptionText = `${title}\n\n${validFacts.map((fact, index) => {
      const factText = typeof fact === 'string' ? fact : (fact.text || 'Interesting fact');
      return `Fact ${index + 1}: ${factText}`;
    }).join('\n\n')}\n\nLike and subscribe for more amazing facts!`;
    
    await fs.writeFile(descriptionFile, descriptionText);
    console.log(`Description saved to ${descriptionFile}`);
    
    // Clean up temporary directory
    try {
      await fs.remove(tempDir);
    } catch (cleanupError) {
      console.error('Error removing temp directory:', cleanupError.message);
    }
    
    // Copy the video file to a simpler name for easier reference
    const simpleName = `${category}_facts.mp4`;
    const simpleOutputPath = path.join(outputDir, simpleName);
    try {
      await fs.copy(outputPath, simpleOutputPath);
      console.log(`Copied video to ${simpleOutputPath} for easy reference`);
    } catch (copyError) {
      console.error('Error copying to simple name:', copyError.message);
    }
    
    return {
      videoPath: outputPath,
      descriptionPath: descriptionFile
    };
  } catch (error) {
    console.error('Error in createFactsImageVideo:', error.message);
    
    // Emergency fallback - create the most basic video possible
    try {
      console.log('EMERGENCY FALLBACK: Creating basic video...');
      
      // Create a super basic video
      const emergencyCommand = `ffmpeg -f lavfi -i color=c=blue:s=1280x720:d=30 -c:v libx264 -pix_fmt yuv420p -y "${outputPath}"`;
      execSync(emergencyCommand, { stdio: 'inherit' });
      
      // Save description to file
      const descriptionFile = `${outputPath}.description.txt`;
      const descriptionText = `${validFacts.length} Amazing ${category.charAt(0).toUpperCase() + category.slice(1)} Facts\n\n${validFacts.map((fact, index) => {
        const factText = typeof fact === 'string' ? fact : (fact.text || 'Interesting fact');
        return `Fact ${index + 1}: ${factText}`;
      }).join('\n\n')}\n\nLike and subscribe for more amazing facts!`;
      
      await fs.writeFile(descriptionFile, descriptionText);
      
      return {
        videoPath: outputPath,
        descriptionPath: descriptionFile
      };
    } catch (emergencyError) {
      console.error('Emergency fallback failed:', emergencyError.message);
      throw error;
    }
  }
}

module.exports = { createFactsImageVideo };


module.exports = { createFactsImageVideo };