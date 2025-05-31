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
    
    console.log(`Creating frames for ${validFacts.length} facts...`);
    
    // Create frame for title (repeat for 3 seconds at 30fps = 90 frames)
    const titleFrames = [];
    for (let i = 0; i < 90; i++) {
      const titleFramePath = path.join(framesDir, `title_${String(i).padStart(4, '0')}.png`);
      await createTextFrame(title, titleFramePath, 'title');
      titleFrames.push(titleFramePath);
    }
    
    // Create frames for each fact (5 seconds each at 30fps = 150 frames per fact)
    const factFrames = [];
    for (let factIndex = 0; factIndex < validFacts.length; factIndex++) {
      const fact = validFacts[factIndex];
      const factText = typeof fact === 'string' ? fact : (fact.text || 'Interesting fact');
      
      console.log(`Creating frames for fact ${factIndex + 1}: ${factText.substring(0, 50)}...`);
      
      for (let frameIndex = 0; frameIndex < 150; frameIndex++) {
        const framePath = path.join(framesDir, `fact_${factIndex}_${String(frameIndex).padStart(4, '0')}.png`);
        await createTextFrame(`Fact ${factIndex + 1}: ${factText}`, framePath, 'fact');
        factFrames.push(framePath);
      }
    }
    
    // Combine all frames
    const allFrames = [...titleFrames, ...factFrames];
    console.log(`Total frames created: ${allFrames.length}`);
    
    // Verify frames exist and have content
    console.log('Verifying frames...');
    for (let i = 0; i < Math.min(5, allFrames.length); i++) {
      const frameExists = await fs.pathExists(allFrames[i]);
      const frameStats = frameExists ? await fs.stat(allFrames[i]) : null;
      console.log(`Frame ${i}: exists=${frameExists}, size=${frameStats ? frameStats.size : 'N/A'} bytes`);
    }
    
    // Method 1: Try using image sequence input (more reliable)
    console.log('Creating video using image sequence method...');
    
    // Copy frames to numbered sequence for FFmpeg
    const sequenceDir = path.join(framesDir, 'sequence');
    await fs.ensureDir(sequenceDir);
    
    for (let i = 0; i < allFrames.length; i++) {
      const seqPath = path.join(sequenceDir, `frame_${String(i).padStart(6, '0')}.png`);
      await fs.copy(allFrames[i], seqPath);
    }
    
    // Create video from image sequence
    const sequencePattern = path.join(sequenceDir, 'frame_%06d.png');
    const imageSequenceCommand = `ffmpeg -framerate 30 -i "${sequencePattern}" -c:v libx264 -pix_fmt yuv420p -y "${outputPath}"`;
    
    console.log(`Executing image sequence command: ${imageSequenceCommand}`);
    
    try {
      execSync(imageSequenceCommand, { stdio: 'inherit' });
      console.log('Image sequence method successful!');
    } catch (seqError) {
      console.error('Image sequence method failed, trying alternative...');
      
      // Method 2: Create individual videos and concatenate
      console.log('Trying individual video concatenation method...');
      
      // Create video for title
      const titleVideoPath = path.join(framesDir, 'title.mp4');
      const titleCommand = `ffmpeg -loop 1 -i "${titleFrames[0]}" -c:v libx264 -t 3 -pix_fmt yuv420p -y "${titleVideoPath}"`;
      execSync(titleCommand, { stdio: 'inherit' });
      
      // Create videos for each fact
      const factVideos = [];
      for (let i = 0; i < validFacts.length; i++) {
        const factVideoPath = path.join(framesDir, `fact_${i}.mp4`);
        const factFramePath = path.join(framesDir, `fact_${i}_0000.png`);
        const factCommand = `ffmpeg -loop 1 -i "${factFramePath}" -c:v libx264 -t 5 -pix_fmt yuv420p -y "${factVideoPath}"`;
        execSync(factCommand, { stdio: 'inherit' });
        factVideos.push(factVideoPath);
      }
      
      // Create concat list for videos
      const videoListPath = path.join(framesDir, 'video_list.txt');
      let videoListContent = `file '${titleVideoPath}'\n`;
      factVideos.forEach(videoPath => {
        videoListContent += `file '${videoPath}'\n`;
      });
      await fs.writeFile(videoListPath, videoListContent);
      
      // Concatenate videos
      const concatCommand = `ffmpeg -f concat -safe 0 -i "${videoListPath}" -c copy -y "${outputPath}"`;
      execSync(concatCommand, { stdio: 'inherit' });
      console.log('Video concatenation method successful!');
    }
    
    // Verify the output video exists and has reasonable size
    const videoExists = await fs.pathExists(outputPath);
    const videoStats = videoExists ? await fs.stat(outputPath) : null;
    console.log(`Output video: exists=${videoExists}, size=${videoStats ? videoStats.size : 'N/A'} bytes`);
    
    if (!videoExists || (videoStats && videoStats.size < 1000)) {
      throw new Error('Output video is missing or too small');
    }
    
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
      await createTextFrame('Facts Video - Check Logs', emergencyFramePath, 'emergency');
      
      // Verify the emergency frame was created
      const frameExists = await fs.pathExists(emergencyFramePath);
      console.log(`Emergency frame created: ${frameExists}`);
      
      if (frameExists) {
        // Create video from the single frame
        const emergencyCommand = `ffmpeg -loop 1 -i "${emergencyFramePath}" -c:v libx264 -t 30 -pix_fmt yuv420p -y "${outputPath}"`;
        execSync(emergencyCommand, { stdio: 'inherit' });
        
        console.log(`Emergency video created at: ${outputPath}`);
      } else {
        // Create a completely basic video without any frames
        const basicCommand = `ffmpeg -f lavfi -i color=c=blue:s=1280x720:d=30 -c:v libx264 -pix_fmt yuv420p -y "${outputPath}"`;
        execSync(basicCommand, { stdio: 'inherit' });
        console.log(`Basic blue video created at: ${outputPath}`);
      }
      
      // Clean up
      await fs.remove(emergencyFrameDir);
      
      // Save description
      const descriptionFile = `${outputPath}.description.txt`;
      const validFacts = (facts && facts.length > 0) ? facts : [{ text: "Video generation encountered issues" }];
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
async function createTextFrame(text, outputPath, frameType = 'fact') {
  try {
    console.log(`Creating ${frameType} frame: ${text.substring(0, 50)}...`);
    
    // Ensure the directory exists
    const dir = path.dirname(outputPath);
    await fs.ensureDir(dir);
    
    // Clean the text for ImageMagick (escape quotes and handle special characters)
    const cleanText = text
      .replace(/"/g, '\\"')
      .replace(/'/g, "\\'")
      .replace(/\$/g, '\\$')
      .replace(/`/g, '\\`');
    
    // Use different settings based on frame type
    let bgColor, textColor, fontSize, gravity;
    
    if (frameType === 'title') {
      bgColor = 'darkblue';
      textColor = 'yellow';
      fontSize = '48';
      gravity = 'center';
    } else {
      bgColor = 'navy';
      textColor = 'white';
      fontSize = '36';
      gravity = 'center';
    }
    
    // Word wrap the text for better display
    const maxCharsPerLine = 50;
    const words = cleanText.split(' ');
    const lines = [];
    let currentLine = '';
    
    for (const word of words) {
      if ((currentLine + word).length > maxCharsPerLine && currentLine.length > 0) {
        lines.push(currentLine.trim());
        currentLine = word + ' ';
      } else {
        currentLine += word + ' ';
      }
    }
    if (currentLine.trim()) {
      lines.push(currentLine.trim());
    }
    
    const wrappedText = lines.join('\\n');
    
    // Create the image with ImageMagick
    const command = `convert -size 1280x720 xc:${bgColor} -fill ${textColor} -pointsize ${fontSize} -gravity ${gravity} -font Arial -annotate +0+0 "${wrappedText}" "${outputPath}"`;
    
    console.log(`ImageMagick command: ${command.substring(0, 100)}...`);
    execSync(command, { stdio: 'pipe' });
    
    // Verify the file was created
    const exists = await fs.pathExists(outputPath);
    const stats = exists ? await fs.stat(outputPath) : null;
    
    if (exists && stats && stats.size > 1000) {
      console.log(`✅ Frame created successfully: ${outputPath} (${stats.size} bytes)`);
      return true;
    } else {
      console.error(`❌ Frame creation failed or file too small: ${exists ? stats.size : 0} bytes`);
      return false;
    }
    
  } catch (error) {
    console.error(`Error creating frame: ${error.message}`);
    
    // Fallback to even simpler image if the text command fails
    try {
      console.log('Using fallback plain colored frame');
      const fallbackCommand = `convert -size 1280x720 xc:darkblue "${outputPath}"`;
      execSync(fallbackCommand, { stdio: 'pipe' });
      
      const exists = await fs.pathExists(outputPath);
      if (exists) {
        console.log(`✅ Fallback frame created: ${outputPath}`);
        return true;
      } else {
        console.error(`❌ Fallback frame creation failed`);
        return false;
      }
    } catch (fallbackError) {
      console.error(`Fallback frame creation failed: ${fallbackError.message}`);
      return false;
    }
  }
}

module.exports = { createFrameBasedVideo };
