/**
 * Frame-by-frame video generator that displays facts as text in the video
 * This creates individual images for each fact, then combines them into a video
 */
const fs = require('fs-extra');
const { execSync } = require('child_process');
const path = require('path');

/**
 * Create a video from facts by generating individual frames
 */
async function createFrameBasedVideo(facts, category, outputPath) {
  console.log('Creating frame-based video with visible facts text...');
  
  try {
    // Ensure the output directory exists
    const outputDir = path.dirname(outputPath);
    await fs.ensureDir(outputDir);
    
    // Create temp directory for frames
    const framesDir = path.join(outputDir, 'frames');
    await fs.ensureDir(framesDir);
    
    // Ensure we have valid facts
    const validFacts = (facts && facts.length > 0) ? facts : [
      { text: "The human brain can process images in as little as 13 milliseconds." },
      { text: "The Earth is not a perfect sphere; it's an oblate spheroid, flattened at the poles." },
      { text: "There are more possible iterations of a game of chess than there are atoms in the universe." },
      { text: "Honey never spoils. Archaeologists have found pots of honey from ancient Egyptian tombs that are over 3,000 years old." },
      { text: "The longest recorded flight of a chicken is 13 seconds." }
    ];
    
    // Format title
    const title = `${validFacts.length} Amazing ${category.charAt(0).toUpperCase() + category.slice(1)} Facts`;
    
    // Create frame for title
    const titleFramePath = path.join(framesDir, '00_title.png');
    await createTextFrame(title, titleFramePath);
    
    // Create a frame for each fact
    const frameFiles = [titleFramePath];
    
    for (let i = 0; i < validFacts.length; i++) {
      const fact = validFacts[i];
      const factText = typeof fact === 'string' ? fact : (fact.text || 'Interesting fact');
      const frameText = `Fact ${i + 1}: ${factText}`;
      const framePath = path.join(framesDir, `${String(i + 1).padStart(2, '0')}_fact.png`);
      
      await createTextFrame(frameText, framePath);
      frameFiles.push(framePath);
    }
    
    // Generate list file for ffmpeg
    const listFilePath = path.join(framesDir, 'frames.txt');
    let listContent = '';
    
    // Duration for each frame (in seconds)
    const titleDuration = 3;
    const factDuration = 5;
    
    // Add each frame with duration to the list
    frameFiles.forEach((framePath, index) => {
      const duration = index === 0 ? titleDuration : factDuration;
      listContent += `file '${framePath}'\nduration ${duration}\n`;
    });
    
    // Add the last frame with a duration (required by FFmpeg)
    listContent += `file '${frameFiles[frameFiles.length - 1]}'\n`;
    
    await fs.writeFile(listFilePath, listContent);
    
    // Create video from frames
    console.log('Creating video from frames...');
    
    const ffmpegCommand = `ffmpeg -f concat -safe 0 -i "${listFilePath}" -vsync vfr -pix_fmt yuv420p -c:v libx264 -r 30 -y "${outputPath}"`;
    
    console.log(`Executing FFmpeg command: ${ffmpegCommand}`);
    execSync(ffmpegCommand, { stdio: 'inherit' });
    
    // Save description to file
    const descriptionFile = `${outputPath}.description.txt`;
    const descriptionText = `${title}\n\n${validFacts.map((fact, index) => {
      const factText = typeof fact === 'string' ? fact : (fact.text || 'Interesting fact');
      return `Fact ${index + 1}: ${factText}`;
    }).join('\n\n')}\n\nLike and subscribe for more amazing facts!`;
    
    await fs.writeFile(descriptionFile, descriptionText);
    console.log(`Description saved to: ${descriptionFile}`);
    
    // Create a copy with a simple name for easy reference
    const simpleName = `${category}_facts.mp4`;
    const simpleOutputPath = path.join(outputDir, simpleName);
    await fs.copy(outputPath, simpleOutputPath);
    console.log(`Copied video to ${simpleOutputPath} for easy reference`);
    
    // Create a "clean" version of the description with simpler name
    const simpleDescFile = `${simpleOutputPath}.description.txt`;
    await fs.copy(descriptionFile, simpleDescFile);
    
    // Clean up temporary files
    try {
      await fs.remove(framesDir);
      console.log('Cleaned up temporary files');
    } catch (cleanupError) {
      console.error('Error cleaning up temp files:', cleanupError.message);
    }
    
    console.log(`Video created successfully at: ${outputPath}`);
    return {
      videoPath: outputPath,
      descriptionPath: descriptionFile
    };
  } catch (error) {
    console.error('Error creating frame-based video:', error.message);
    
    // Emergency fallback - create a basic video with a single frame
    try {
      console.log('Using emergency fallback - creating video with a single frame');
      
      // Create a simple frame with title text
      const emergencyFrameDir = path.join(outputDir, 'emergency_frame');
      await fs.ensureDir(emergencyFrameDir);
      
      const emergencyFramePath = path.join(emergencyFrameDir, 'frame.png');
      await createTextFrame('Facts Video', emergencyFramePath);
      
      // Create video from the single frame
      const emergencyCommand = `ffmpeg -loop 1 -i "${emergencyFramePath}" -c:v libx264 -t 30 -pix_fmt yuv420p -y "${outputPath}"`;
      execSync(emergencyCommand, { stdio: 'inherit' });
      
      // Clean up
      await fs.remove(emergencyFrameDir);
      
      console.log(`Emergency video created at: ${outputPath}`);
      
      // Save description
      const descriptionFile = `${outputPath}.description.txt`;
      await fs.writeFile(descriptionFile, `Facts Video\n\n${validFacts.map((fact, index) => {
        const factText = typeof fact === 'string' ? fact : (fact.text || 'Interesting fact');
        return `Fact ${index + 1}: ${factText}`;
      }).join('\n\n')}`);
      
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

/**
 * Create a single frame with text
 */
async function createTextFrame(text, outputPath) {
  try {
    console.log(`Creating frame with text: ${text.substring(0, 30)}...`);
    
    // Use a very simple ImageMagick command - no fancy options
    const command = `convert -size 1280x720 xc:darkblue -fill white -pointsize 40 -gravity center -annotate +0+0 "${text.replace(/"/g, '\\"')}" "${outputPath}"`;
    
    execSync(command, { stdio: 'inherit' });
    console.log(`Created frame at: ${outputPath}`);
    return true;
  } catch (error) {
    console.error(`Error creating frame: ${error.message}`);
    
    // Fallback to even simpler image if the text command fails
    try {
      console.log('Using fallback plain blue frame');
      const fallbackCommand = `convert -size 1280x720 xc:darkblue "${outputPath}"`;
      execSync(fallbackCommand, { stdio: 'inherit' });
      return true;
    } catch (fallbackError) {
      console.error(`Fallback frame creation failed: ${fallbackError.message}`);
      return false;
    }
  }
}

module.exports = { createFrameBasedVideo };