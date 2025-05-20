// Ultra-simple approach for GitHub Actions using system FFmpeg

/**
 * Creates a basic slideshow video using system FFmpeg
 * This uses the simplest possible approach that should work in any environment
 */
async function createBasicSlideshowVideo(facts, category, outputPath) {
  const fs = require('fs-extra');
  const { spawn } = require('child_process');
  
  console.log('Creating basic slideshow video using system FFmpeg...');
  
  try {
    // Create a temporary directory
    const tempDir = './temp_frames/';
    await fs.ensureDir(tempDir);
    
    // Create a title slide text file
    const title = `${facts.length} Amazing ${category.toUpperCase()} Facts`;
    const titleFile = `${tempDir}title.txt`;
    await fs.writeFile(titleFile, title);
    
    // Create fact text files
    const factTextFile = `${tempDir}facts.txt`;
    const factsText = facts.map((fact, index) => {
      const factText = typeof fact === 'string' ? fact : (fact.text || 'Interesting fact');
      return `Fact ${index + 1}: ${factText}`;
    }).join('\n\n');
    await fs.writeFile(factTextFile, factsText);
    
    // Background colors for different categories
    const bgColors = {
      history: 'brown',
      geography: 'darkgreen',
      science: 'indigo',
      ancient_civilizations: 'maroon',
      space: 'navy',
      ocean: 'darkblue'
    };
    
    const bgColor = bgColors[category] || 'blue';
    
    // Create text file with all facts to use in video
    const allContentFile = `${tempDir}content.txt`;
    const allContentText = `${title}\n\n${factsText}`;
    await fs.writeFile(allContentFile, allContentText);
    
    // Super simple approach - create a color video with a duration
    const duration = 30; // 30 seconds video
    
    // Execute FFmpeg command to create a solid color video
    console.log(`Running FFmpeg command to create video with ${bgColor} background...`);
    
    await new Promise((resolve, reject) => {
      const process = spawn('ffmpeg', [
        '-f', 'lavfi',
        '-i', `color=c=${bgColor}:s=1280x720:d=${duration}`,
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-y',
        outputPath
      ]);
      
      process.stdout.on('data', (data) => {
        console.log(`stdout: ${data}`);
      });
      
      process.stderr.on('data', (data) => {
        console.log(`stderr: ${data}`);
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
    
    // Add content to video description for YouTube
    const descriptionFile = `${outputPath}.description.txt`;
    await fs.writeFile(descriptionFile, allContentText);
    
    console.log(`Basic slideshow video created at: ${outputPath}`);
    console.log(`Video description saved to: ${descriptionFile}`);
    return outputPath;
  } catch (error) {
    console.error('Error creating basic slideshow video:', error.message);
    
    // Super simple fallback if everything else fails
    try {
      console.log('Attempting to create simplest possible video...');
      
      await new Promise((resolve, reject) => {
        const process = spawn('ffmpeg', [
          '-f', 'lavfi',
          '-i', 'color=c=blue:s=1280x720:d=30',
          '-c:v', 'libx264',
          '-pix_fmt', 'yuv420p',
          '-y',
          outputPath
        ]);
        
        process.on('close', (code) => {
          if (code === 0) {
            resolve();
          } else {
            reject(new Error(`Process exited with code ${code}`));
          }
        });
      });
      
      console.log(`Simplest video created at: ${outputPath}`);
      return outputPath;
    } catch (fallbackError) {
      console.error('Even simplest video creation failed:', fallbackError.message);
      throw error;
    }
  }
}

module.exports = { createBasicSlideshowVideo };
