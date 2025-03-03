import React from 'react';
import styled from 'styled-components';

const Loader = () => {
  return (
    <StyledWrapper>
      <div className="boxes">
        <div className="box">
          <div />
          <div />
          <div />
          <div />
        </div>
        <div className="box">
          <div />
          <div />
          <div />
          <div />
        </div>
        <div className="box">
          <div />
          <div />
          <div />
          <div />
        </div>
        <div className="box">
          <div />
          <div />
          <div />
          <div />
        </div>
      </div>
    </StyledWrapper>
  );
};

const StyledWrapper = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.8);
  z-index: 1000;

  .boxes {
    --size: 32px;
    --duration: 800ms;
    height: calc(var(--size) * 2);
    width: calc(var(--size) * 3);
    position: relative;
    transform-style: preserve-3d;
    transform-origin: 50% 50%;
    transform: rotateX(60deg) rotateZ(45deg) rotateY(0deg) translateZ(0px);
  }

  .boxes .box {
    width: var(--size);
    height: var(--size);
    position: absolute;
    transform-style: preserve-3d;
  }

  .boxes .box > div {
    --primary: #5C8DF6;
    --secondary: #145af2;
    --background: var(--primary);
    --top: auto;
    --right: auto;
    --bottom: auto;
    --left: auto;
    --translateZ: calc(var(--size) / 2);
    --rotateY: 0deg;
    --rotateX: 0deg;
    position: absolute;
    width: 100%;
    height: 100%;
    background: var(--background);
    top: var(--top);
    right: var(--right);
    bottom: var(--bottom);
    left: var(--left);
    transform: rotateY(var(--rotateY)) rotateX(var(--rotateX)) translateZ(var(--translateZ));
  }

  /* Box positions and animations */
  .boxes .box:nth-child(1) {
    transform: translate(100%, 0);
    animation: box1 var(--duration) linear infinite;
  }

  .boxes .box:nth-child(2) {
    transform: translate(0, 100%);
    animation: box2 var(--duration) linear infinite;
  }

  .boxes .box:nth-child(3) {
    transform: translate(100%, 100%);
    animation: box3 var(--duration) linear infinite;
  }

  .boxes .box:nth-child(4) {
    transform: translate(200%, 0);
    animation: box4 var(--duration) linear infinite;
  }

  /* Color adjustments */
  .boxes .box > div:nth-child(1) {
    --background: var(--primary);
  }

  .boxes .box > div:nth-child(2) {
    --background: var(--secondary);
    --rotateY: 90deg;
  }

  .boxes .box > div:nth-child(3) {
    --background: #447cf5;
    --rotateX: -90deg;
  }

  .boxes .box > div:nth-child(4) {
    --background: #DBE3F4;
    --translateZ: calc(var(--size) * 3 * -1);
  }

  /* Animations */
  @keyframes box1 {
    0%, 50% { transform: translate(100%, 0); }
    100% { transform: translate(200%, 0); }
  }

  @keyframes box2 {
    0% { transform: translate(0, 100%); }
    50% { transform: translate(0, 0); }
    100% { transform: translate(100%, 0); }
  }

  @keyframes box3 {
    0%, 50% { transform: translate(100%, 100%); }
    100% { transform: translate(0, 100%); }
  }

  @keyframes box4 {
    0% { transform: translate(200%, 0); }
    50% { transform: translate(200%, 100%); }
    100% { transform: translate(100%, 100%); }
  }

  /* Mobile optimization */
  @media (max-width: 768px) {
    .boxes {
      --size: 24px;
    }
  }
`;

export default Loader;