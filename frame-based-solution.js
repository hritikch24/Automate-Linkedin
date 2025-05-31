/**
 * Enhanced Frame-by-frame video generator with AI content, images, and voice
 */
const fs = require('fs-extra');
const { execSync } = require('child_process');
const path = require('path');
const axios = require('axios');

/**
 * Enhanced video creation with AI-generated content, images, and voice
 */
async function createFrameBasedVideo(facts, category, outputPath) {
  console.log('Creating enhanced video with AI content, images, and voice...');
  
  try {
    const outputDir = path.dirname(outputPath);
    await fs.ensureDir(outputDir);
    
    // Create directories for assets
    const framesDir = path.join(outputDir, 'frames');
    const imagesDir = path.join(outputDir, 'images');
    const audioDir = path.join(outputDir, 'audio');
    
    await fs.ensureDir(framesDir);
    await fs.ensureDir(imagesDir);
    await fs.ensureDir(audioDir);
    
    // Generate enhanced content using AI
    const enhancedContent = await generateEnhancedContent(facts, category);
    
    console.log(`Creating enhanced video: "${enhancedContent.title}"`);
    
    // Download background images for each fact
    const backgroundImages = await downloadBackgroundImages(enhancedContent.facts, category, imagesDir);
    
    // Generate voice narration
    const audioFiles = await generateVoiceNarration(enhancedContent, audioDir);
    
    // Create enhanced frames
    const frameSequence = await createEnhancedFrames(enhancedContent, backgroundImages, framesDir);
    
    // Combine frames with audio to create final video
    const finalVideo = await combineFramesWithAudio(frameSequence, audioFiles, outputPath);
    
    // Save metadata
    await saveVideoMetadata(enhancedContent, outputPath);
    
    console.log(`Enhanced video created successfully: ${outputPath}`);
    return {
      videoPath: outputPath,
      title: enhancedContent.title,
      description: enhancedContent.description,
      tags: enhancedContent.tags
    };
    
  } catch (error) {
    console.error('Enhanced video creation failed:', error.message);
    // Fallback to simpler version
    return await createSimpleVideo(facts, category, outputPath);
  }
}

/**
 * Generate enhanced content using AI
 */
async function generateEnhancedContent(facts, category) {
  console.log(`Generating enhanced content for ${category}...`);
  
  const geminiApiKey = process.env.GEMINI_API_KEY;
  
  // Generate catchy title
  const titlePrompt = `Create a catchy, engaging YouTube title for a facts video about ${category}. 
  The title should be:
  - Under 60 characters
  - Include numbers (like "7 Mind-Blowing" or "5 Incredible")
  - Use power words like: Amazing, Incredible, Mind-Blowing, Shocking, Unbelievable
  - Be click-worthy but not clickbait
  - Appeal to curiosity
  
  Examples: "7 Mind-Blowing Ocean Facts That Will Shock You", "5 Incredible History Facts You Never Learned"
  
  Category: ${category}
  Number of facts: ${facts.length}
  
  Return only the title, nothing else.`;
  
  // Generate enhanced facts with hooks
  const factsPrompt = `Transform these facts about ${category} into engaging, hook-filled content for YouTube shorts:

  Original facts: ${facts.map(f => typeof f === 'string' ? f : f.text).join('\n')}
  
  For each fact, create:
  1. A hook opener (e.g., "You won't believe this...", "Scientists were shocked when...")
  2. The main fact (rewritten to be more engaging)
  3. A wow factor ending (e.g., "That's absolutely incredible!", "Mind = blown!")
  
  Make each fact 2-3 sentences, exciting, and perfect for video narration.
  Return as JSON array with objects containing: hook, fact, wow_factor`;
  
  // Generate description and tags
  const metaPrompt = `Create YouTube metadata for a ${category} facts video:
  
  Generate:
  1. A compelling description (150-200 words) with emojis
  2. 10 relevant hashtags for maximum reach
  3. 5 keyword tags
  
  Return as JSON: {"description": "...", "hashtags": [...], "tags": [...]}`;
  
  try {
    // Generate title
    const titleResponse = await callGeminiAPI(titlePrompt);
    const title = titleResponse.trim().replace(/['"]/g, '');
    
    // Generate enhanced facts
    const factsResponse = await callGeminiAPI(factsPrompt);
    const enhancedFacts = parseGeminiJSON(factsResponse, facts.map(f => ({
      hook: "Did you know...",
      fact: typeof f === 'string' ? f : f.text,
      wow_factor: "Amazing!"
    })));
    
    // Generate metadata
    const metaResponse = await callGeminiAPI(metaPrompt);
    const metadata = parseGeminiJSON(metaResponse, {
      description: `Amazing ${category} facts that will blow your mind! 🤯`,
      hashtags: [`#${category}`, '#facts', '#didyouknow'],
      tags: [category, 'facts', 'amazing']
    });
    
    return {
      title,
      facts: enhancedFacts,
      description: metadata.description,
      hashtags: metadata.hashtags,
      tags: metadata.tags
    };
    
  } catch (error) {
    console.error('AI content generation failed:', error.message);
    // Fallback to basic content
    return {
      title: `${facts.length} Amazing ${category.charAt(0).toUpperCase() + category.slice(1)} Facts`,
      facts: facts.map(f => ({
        hook: "Here's something incredible:",
        fact: typeof f === 'string' ? f : f.text,
        wow_factor: "Absolutely amazing!"
      })),
      description: `Discover amazing facts about ${category}!`,
      hashtags: [`#${category}`, '#facts', '#amazing'],
      tags: [category, 'facts', 'interesting']
    };
  }
}

/**
 * Call Gemini API helper
 */
async function callGeminiAPI(prompt) {
  const response = await axios.post(
    'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent',
    {
      contents: [{ parts: [{ text: prompt }] }],
      generationConfig: {
        temperature: 0.7,
        topK: 40,
        topP: 0.95,
        maxOutputTokens: 1024,
      }
    },
    {
      headers: {
        'Content-Type': 'application/json',
        'x-goog-api-key': process.env.GEMINI_API_KEY
      }
    }
  );
  
  return response.data.candidates[0].content.parts[0].text;
}

/**
 * Parse JSON from Gemini response with fallback
 */
function parseGeminiJSON(response, fallback) {
  try {
    const jsonMatch = response.match(/\{[\s\S]*\}|\[[\s\S]*\]/);
    return jsonMatch ? JSON.parse(jsonMatch[0]) : fallback;
  } catch (error) {
    console.error('Failed to parse Gemini JSON:', error.message);
    return fallback;
  }
}

/**
 * Download background images for facts
 */
async function downloadBackgroundImages(facts, category, imagesDir) {
  console.log('Downloading background images...');
  
  const images = [];
  
  // Category-specific image searches
  const categoryImages = {
    history: ['ancient castle', 'historical monument', 'old manuscript', 'vintage map'],
    science: ['laboratory', 'DNA helix', 'space nebula', 'scientific equipment'],
    geography: ['mountain landscape', 'world map', 'ocean waves', 'desert dunes'],
    space: ['galaxy', 'planets', 'astronaut', 'space station'],
    ocean: ['coral reef', 'deep sea', 'marine life', 'underwater cave'],
    ancient_civilizations: ['pyramid', 'ancient ruins', 'archaeological site', 'ancient art']
  };
  
  const searchTerms = categoryImages[category] || ['abstract background', 'science', 'nature', 'technology'];
  
  // Create gradient backgrounds if image download fails
  for (let i = 0; i < facts.length; i++) {
    const imagePath = path.join(imagesDir, `bg_${i}.jpg`);
    
    try {
      // Try to create attractive gradient backgrounds using ImageMagick
      const gradients = [
        'gradient:purple-blue',
        'gradient:blue-cyan',
        'gradient:green-blue',
        'gradient:orange-red',
        'gradient:pink-purple',
        'gradient:yellow-orange'
      ];
      
      const gradient = gradients[i % gradients.length];
      const command = `convert -size 1280x720 "${gradient}" -blur 0x8 "${imagePath}"`;
      execSync(command, { stdio: 'pipe' });
      
      images.push(imagePath);
      console.log(`Created gradient background ${i + 1}`);
      
    } catch (error) {
      console.error(`Failed to create background ${i}:`, error.message);
      // Fallback to solid color
      const colors = ['#1e3a8a', '#7c2d12', '#166534', '#7c2d12', '#581c87', '#b45309'];
      const color = colors[i % colors.length];
      const fallbackCommand = `convert -size 1280x720 xc:"${color}" "${imagePath}"`;
      execSync(fallbackCommand, { stdio: 'pipe' });
      images.push(imagePath);
    }
  }
  
  return images;
}

/**
 * Generate voice narration using text-to-speech
 */
async function generateVoiceNarration(content, audioDir) {
  console.log('Generating voice narration...');
  
  const audioFiles = [];
  
  try {
    // Title narration
    const titleText = `Welcome to our amazing facts video: ${content.title}`;
    const titleAudioPath = path.join(audioDir, 'title.wav');
    await generateSpeech(titleText, titleAudioPath);
    audioFiles.push({ file: titleAudioPath, duration: 3 });
    
    // Fact narrations
    for (let i = 0; i < content.facts.length; i++) {
      const fact = content.facts[i];
      const fullText = `${fact.hook} ${fact.fact} ${fact.wow_factor}`;
      const factAudioPath = path.join(audioDir, `fact_${i}.wav`);
      await generateSpeech(fullText, factAudioPath);
      audioFiles.push({ file: factAudioPath, duration: 6 });
    }
    
    return audioFiles;
    
  } catch (error) {
    console.error('Voice generation failed:', error.message);
    return []; // Return empty array to create silent video
  }
}

/**
 * Generate speech using espeak (fallback TTS)
 */
async function generateSpeech(text, outputPath) {
  try {
    // Clean text for speech synthesis
    const cleanText = text.replace(/[^\w\s.,!?-]/g, '').substring(0, 500);
    
    // Use espeak with better voice settings
    const command = `espeak -v en+f3 -s 150 -p 50 -a 100 "${cleanText}" -w "${outputPath}"`;
    execSync(command, { stdio: 'pipe' });
    
    // Convert to better format if needed
    if (await fs.pathExists(outputPath)) {
      const mp3Path = outputPath.replace('.wav', '.mp3');
      const convertCommand = `ffmpeg -i "${outputPath}" -acodec mp3 -ab 128k -y "${mp3Path}"`;
      try {
        execSync(convertCommand, { stdio: 'pipe' });
        await fs.remove(outputPath);
        await fs.move(mp3Path, outputPath);
      } catch (convertError) {
        // Keep original wav file
        console.log('Keeping original WAV format');
      }
    }
    
    console.log(`Generated speech: ${outputPath}`);
  } catch (error) {
    console.error(`Speech generation failed for: ${text.substring(0, 50)}...`);
    // Create silent audio file
    const silentCommand = `ffmpeg -f lavfi -i anullsrc=r=44100:cl=stereo -t 5 -y "${outputPath}"`;
    execSync(silentCommand, { stdio: 'pipe' });
  }
}

/**
 * Create enhanced frames with better typography and design
 */
async function createEnhancedFrames(content, backgroundImages, framesDir) {
  console.log('Creating enhanced frames with better design...');
  
  const frameSequence = [];
  
  // Enhanced title frame (4 seconds)
  for (let i = 0; i < 120; i++) { // 30fps * 4sec
    const framePath = path.join(framesDir, `title_${String(i).padStart(4, '0')}.png`);
    await createEnhancedTitleFrame(content.title, framePath, i);
    frameSequence.push(framePath);
  }
  
  // Enhanced fact frames (6 seconds each)
  for (let factIndex = 0; factIndex < content.facts.length; factIndex++) {
    const fact = content.facts[factIndex];
    const bgImage = backgroundImages[factIndex] || backgroundImages[0];
    
    for (let frameIndex = 0; frameIndex < 180; frameIndex++) { // 30fps * 6sec
      const framePath = path.join(framesDir, `fact_${factIndex}_${String(frameIndex).padStart(4, '0')}.png`);
      await createEnhancedFactFrame(fact, bgImage, framePath, frameIndex, factIndex + 1);
      frameSequence.push(framePath);
    }
  }
  
  return frameSequence;
}

/**
 * Create enhanced title frame with animation effects
 */
async function createEnhancedTitleFrame(title, outputPath, frameNumber) {
  try {
    // Create animated title with fade-in effect
    const opacity = Math.min(100, (frameNumber * 3));
    const scale = Math.min(100, 80 + (frameNumber * 0.5));
    
    const command = `convert -size 1280x720 gradient:"#1a1a2e-#16213e" \\
      -font Arial-Bold -pointsize 52 -fill "rgba(255,255,255,${opacity}%)" \\
      -gravity center -annotate +0-50 "${title.replace(/"/g, '\\"')}" \\
      -font Arial -pointsize 24 -fill "rgba(255,215,0,${opacity}%)" \\
      -gravity center -annotate +0+50 "Amazing Facts Await!" \\
      "${outputPath}"`;
    
    execSync(command, { stdio: 'pipe' });
  } catch (error) {
    // Fallback
    const fallbackCommand = `convert -size 1280x720 xc:"#1a1a2e" -fill white -pointsize 40 -gravity center -annotate +0+0 "${title.replace(/"/g, '\\"')}" "${outputPath}"`;
    execSync(fallbackCommand, { stdio: 'pipe' });
  }
}

/**
 * Create enhanced fact frame with background and better typography
 */
async function createEnhancedFactFrame(fact, backgroundImage, outputPath, frameIndex, factNumber) {
  try {
    // Determine which text to show based on frame progression
    let displayText = '';
    const totalFrames = 180;
    const hookFrames = 60;
    const factFrames = 90;
    const wowFrames = 30;
    
    if (frameIndex < hookFrames) {
      displayText = fact.hook;
    } else if (frameIndex < hookFrames + factFrames) {
      displayText = `Fact ${factNumber}: ${fact.fact}`;
    } else {
      displayText = fact.wow_factor;
    }
    
    // Wrap text for better display
    const wrappedText = wrapText(displayText, 45);
    
    // Create frame with background and text overlay
    const command = `convert "${backgroundImage}" \\
      -resize 1280x720! \\
      -fill "rgba(0,0,0,0.6)" -draw "rectangle 0,500,1280,720" \\
      -font Arial-Bold -pointsize 36 -fill white -stroke black -strokewidth 2 \\
      -gravity south -annotate +0+100 "${wrappedText}" \\
      -font Arial -pointsize 24 -fill yellow \\
      -gravity southeast -annotate +20+20 "Fact ${factNumber}" \\
      "${outputPath}"`;
    
    execSync(command, { stdio: 'pipe' });
    
  } catch (error) {
    console.error(`Error creating enhanced frame: ${error.message}`);
    // Simple fallback
    const fallbackCommand = `convert -size 1280x720 xc:"#2d3748" -fill white -pointsize 32 -gravity center -annotate +0+0 "${displayText.replace(/"/g, '\\"')}" "${outputPath}"`;
    execSync(fallbackCommand, { stdio: 'pipe' });
  }
}

/**
 * Wrap text for better display
 */
function wrapText(text, maxLength) {
  const words = text.split(' ');
  const lines = [];
  let currentLine = '';
  
  words.forEach(word => {
    if ((currentLine + word).length > maxLength && currentLine.length > 0) {
      lines.push(currentLine.trim());
      currentLine = word + ' ';
    } else {
      currentLine += word + ' ';
    }
  });
  
  if (currentLine.trim()) {
    lines.push(currentLine.trim());
  }
  
  return lines.join('\\n');
}

/**
 * Combine frames with audio
 */
async function combineFramesWithAudio(frameSequence, audioFiles, outputPath) {
  console.log('Combining frames with audio...');
  
  try {
    // Create video from frame sequence
    const tempVideoPath = outputPath.replace('.mp4', '_temp.mp4');
    const framePattern = path.join(path.dirname(frameSequence[0]), 'sequence_%06d.png');
    
    // Copy frames to sequential naming
    for (let i = 0; i < frameSequence.length; i++) {
      const seqPath = path.join(path.dirname(frameSequence[0]), `sequence_${String(i).padStart(6, '0')}.png`);
      await fs.copy(frameSequence[i], seqPath);
    }
    
    // Create video from frames
    const videoCommand = `ffmpeg -framerate 30 -i "${framePattern}" -c:v libx264 -pix_fmt yuv420p -y "${tempVideoPath}"`;
    execSync(videoCommand, { stdio: 'inherit' });
    
    // Add audio if available
    if (audioFiles.length > 0) {
      // Concatenate audio files
      const audioListPath = path.join(path.dirname(outputPath), 'audio_list.txt');
      const audioListContent = audioFiles.map(audio => `file '${audio.file}'`).join('\n');
      await fs.writeFile(audioListPath, audioListContent);
      
      const concatenatedAudioPath = path.join(path.dirname(outputPath), 'full_audio.wav');
      const audioCommand = `ffmpeg -f concat -safe 0 -i "${audioListPath}" -c copy -y "${concatenatedAudioPath}"`;
      execSync(audioCommand, { stdio: 'pipe' });
      
      // Combine video with audio
      const finalCommand = `ffmpeg -i "${tempVideoPath}" -i "${concatenatedAudioPath}" -c:v copy -c:a aac -shortest -y "${outputPath}"`;
      execSync(finalCommand, { stdio: 'inherit' });
      
      // Cleanup
      await fs.remove(tempVideoPath);
      await fs.remove(concatenatedAudioPath);
      await fs.remove(audioListPath);
    } else {
      // No audio, just rename temp video
      await fs.move(tempVideoPath, outputPath);
    }
    
    console.log(`Final video created: ${outputPath}`);
    return outputPath;
    
  } catch (error) {
    console.error('Error combining frames with audio:', error.message);
    throw error;
  }
}

/**
 * Save video metadata
 */
async function saveVideoMetadata(content, outputPath) {
  const metadataPath = `${outputPath}.metadata.json`;
  const metadata = {
    title: content.title,
    description: content.description,
    hashtags: content.hashtags,
    tags: content.tags,
    facts: content.facts,
    createdAt: new Date().toISOString()
  };
  
  await fs.writeJson(metadataPath, metadata, { spaces: 2 });
  console.log(`Metadata saved: ${metadataPath}`);
}

/**
 * Fallback to simple video creation
 */
async function createSimpleVideo(facts, category, outputPath) {
  console.log('Using simple video fallback...');
  
  // Use original simple method
  const outputDir = path.dirname(outputPath);
  const framesDir = path.join(outputDir, 'simple_frames');
  await fs.ensureDir(framesDir);
  
  // Create basic frames
  const title = `${facts.length} Amazing ${category.charAt(0).toUpperCase() + category.slice(1)} Facts`;
  const titleFramePath = path.join(framesDir, 'title.png');
  
  const command = `convert -size 1280x720 xc:darkblue -fill white -pointsize 40 -gravity center -annotate +0+0 "${title}" "${titleFramePath}"`;
  execSync(command, { stdio: 'pipe' });
  
  // Create simple video
  const videoCommand = `ffmpeg -loop 1 -i "${titleFramePath}" -c:v libx264 -t 30 -pix_fmt yuv420p -y "${outputPath}"`;
  execSync(videoCommand, { stdio: 'inherit' });
  
  return {
    videoPath: outputPath,
    title: title,
    description: `Amazing ${category} facts!`,
    tags: [category, 'facts']
  };
}

module.exports = { createFrameBasedVideo };