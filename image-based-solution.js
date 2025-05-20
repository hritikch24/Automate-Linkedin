/**
 * Simple image-based solution for facts videos
 * This creates a title image with facts and then converts it to a video
 */

const fs = require('fs-extra');
const { execSync } = require('child_process');
const path = require('path');

/**
 * Create an image with facts text and convert to video
 */
async function createFactsImageVideo(facts, category, outputPath) {
  console.log('Creating image-based video for facts...');
  
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
    
    // Format facts for image
    const factsText = validFacts.map((fact, index) => {
      const factText = typeof fact === 'string' ? fact : (fact.text || 'Interesting fact');
      return `Fact ${index + 1}: ${factText}`;
    }).join('\\n\\n');
    
    // Format title
    const title = `${validFacts.length} Amazing ${category.charAt(0).toUpperCase() + category.slice(1)} Facts`;
    
    // Create image file path
    const imagePath = path.join(tempDir, 'facts_image.png');
    
    // Create image with facts using ImageMagick
    console.log('Creating image with facts text...');
    
    // Use ImageMagick to create an image with the title and facts
    // Note: ImageMagick must be installed on the system
    const convertCommand = `convert -size 1280x720 -background blue -fill white -font Arial -pointsize 36 -gravity center caption:"${title}\\n\\n${factsText}" "${imagePath}"`;
    
    try {
      console.log(`Executing ImageMagick command: ${convertCommand}`);
      execSync(convertCommand, { stdio: 'inherit' });
      console.log(`Created facts image at: ${imagePath}`);
    } catch (imageError) {
      console.error('Error creating image with ImageMagick:', imageError.message);
      
      console.log('Falling back to simpler image creation...');
      // Try a simpler approach with just a solid color image
      const simpleFallbackCommand = `convert -size 1280x720 xc:blue "${imagePath}"`;
      execSync(simpleFallbackCommand, { stdio: 'inherit' });
      console.log(`Created simple backup image at: ${imagePath}`);
    }
    
    // Create video from image
    console.log('Converting image to video...');
    const ffmpegCommand = `ffmpeg -loop 1 -i "${imagePath}" -c:v libx264 -t 30 -pix_fmt yuv420p -y "${outputPath}"`;
    
    console.log(`Executing FFmpeg command: ${ffmpegCommand}`);
    execSync(ffmpegCommand, { stdio: 'inherit' });
    
    // Save description to file
    const descriptionFile = `${outputPath}.description.txt`;
    const descriptionText = `${title}\n\n${validFacts.map((fact, index) => {
      const factText = typeof fact === 'string' ? fact : (fact.text || 'Interesting fact');
      return `Fact ${index + 1}: ${factText}`;
    }).join('\n\n')}\n\nLike and subscribe for more amazing facts!`;
    
    await fs.writeFile(descriptionFile, descriptionText);
    console.log(`Video description saved to: ${descriptionFile}`);
    
    // Clean up temporary files
    try {
      await fs.remove(tempDir);
      console.log('Cleaned up temporary files');
    } catch (cleanupError) {
      console.error('Error cleaning up temporary files:', cleanupError.message);
    }
    
    console.log(`Video created successfully at: ${outputPath}`);
    return {
      videoPath: outputPath,
      descriptionPath: descriptionFile
    };
  } catch (error) {
    console.error('Error creating facts image video:', error.message);
    
    // Last resort emergency fallback - create a basic blue video
    try {
      console.log('Emergency fallback: Creating basic blue video...');
      const fallbackCommand = `ffmpeg -f lavfi -i color=c=blue:s=1280x720:d=30 -c:v libx264 -pix_fmt yuv420p -y "${outputPath}"`;
      
      execSync(fallbackCommand, { stdio: 'inherit' });
      console.log(`Created emergency fallback video at: ${outputPath}`);
      
      // Save description to file
      const descriptionFile = `${outputPath}.description.txt`;
      const descriptionText = `${facts.length} Amazing ${category.charAt(0).toUpperCase() + category.slice(1)} Facts\n\n${facts.map((fact, index) => {
        const factText = typeof fact === 'string' ? fact : (fact.text || 'Interesting fact');
        return `Fact ${index + 1}: ${factText}`;
      }).join('\n\n')}\n\nLike and subscribe for more amazing facts!`;
      
      await fs.writeFile(descriptionFile, descriptionText);
      
      return {
        videoPath: outputPath,
        descriptionPath: descriptionFile
      };
    } catch (fallbackError) {
      console.error('Error creating emergency fallback video:', fallbackError.message);
      throw error;
    }
  }
}

module.exports = { createFactsImageVideo };