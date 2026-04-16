import { useState, useEffect } from 'react'

const WORDS = ['Intelligence', 'Insights', 'Predictions', 'Decisions', 'Analysis']

/**
 * Looping typewriter component — renders one word at a time with
 * smooth typing + deleting and a blinking cursor.
 *
 * Usage:  <TypingText />
 */
export function TypingText() {
  const [text, setText]           = useState('')
  const [wordIndex, setWordIndex] = useState(0)
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    const currentWord = WORDS[wordIndex]
    const speed = isDeleting ? 55 : 100

    const timer = setTimeout(() => {
      if (!isDeleting) {
        // Typing forward
        setText(currentWord.substring(0, text.length + 1))

        if (text === currentWord) {
          // Finished typing — pause then start deleting
          setTimeout(() => setIsDeleting(true), 1400)
        }
      } else {
        // Deleting
        setText(currentWord.substring(0, text.length - 1))

        if (text === '') {
          setIsDeleting(false)
          setWordIndex(prev => (prev + 1) % WORDS.length)
        }
      }
    }, speed)

    return () => clearTimeout(timer)
  }, [text, isDeleting, wordIndex])

  return (
    <span className="typing-text">
      {text}
      <span className="typing-cursor" aria-hidden="true">|</span>
    </span>
  )
}
