import { useRef } from "react";
import classes from "./styles.module.css";

const NavMenu = ({ isOpen, setIsOpen, setIsScrollingDisabled }) => {
  const ref = useRef();
  const refBg = useRef();

  // menu close function
  const clickHandler = () => {
    ref.current.classList.add(classes.menuClose);
    refBg.current.classList.add(classes.bgFadeOut);
    setTimeout(() => {
      setIsOpen(!isOpen);
      setIsScrollingDisabled(false);
    }, 500);
  };

  return (
    <>
      {/* menu items */}
      <div ref={ref} className={`w-[400px] h-[100vh] z-[10] fixed left-0 top-0 bg-white opacity-[1] ${classes.menuOpen}`}></div>

      {/* menu background */}
      <div ref={refBg} onClick={clickHandler} className={`w-full h-[100vh] z-[9] fixed left-0 top-0 bg-[rgba(0,0,0,0.5)] ${classes.bgFadeIn}`}></div>
    </>
  );
};

export default NavMenu;
