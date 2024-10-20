import { HiMagnifyingGlass } from "react-icons/hi2";
import classes from "./styles.module.css";
import { useRef, useState } from "react";

const SearchBar = () => {
  const ref = useRef();
  const containerRef = useRef();
  const [isVisible, setIsVisible] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [direction, setDirection] = useState("rtl");

  // open the search function
  const clickHandler = () => {
    setIsVisible(!isVisible);
    ref.current.classList.remove("hidden");
    ref.current.classList.add(classes.searchShow);
    ref.current.classList.remove(classes.searchClose);
    ref.current.parentElement.classList.add("border-b-[1px]");
    ref.current.parentElement.children[1].children[0].classList.add("text-[rgb(220,177,74)]");
    setTimeout(() => {
      ref.current.children[0].focus();
    }, 300);
  };

  // close the search function
  document.addEventListener("click", (event) => {
    if (isVisible && !containerRef.current.contains(event.target)) {
      setIsVisible(!isVisible);
      ref.current.classList.remove(classes.searchShow);
      ref.current.classList.add(classes.searchClose);
      ref.current.parentElement.classList.remove("border-b-[1px]");
      ref.current.parentElement.children[1].children[0].classList.remove("text-[rgb(220,177,74)]");
      setTimeout(() => {
        ref.current.children[0].value = "";
        ref.current.classList.add("hidden");
        setDirection("rtl");
      }, 300);
    }
  });

  // search bar direction & input value function
  const handleInputChange = (event) => {
    const value = event.target.value;
    setInputValue(value);

    // Check the direction based on the current input value
    if (/\d/.test(value) || /^[\u0600-\u06FF]/.test(value)) {
      setDirection("rtl"); // Set direction to RTL if numbers or Persian characters are detected
    } else if (!value) {
      setDirection("rtl");
    } else {
      setDirection("ltr"); // Set direction to LTR for other characters
    }
  };

  return (
    <>
      <div className="w-full h-full flex justify-start items-center">
        <div ref={containerRef} className="w-fit h-[50px] flexRow justify-between items-center py-[10x] gap-[10px] border-b-[rgb(220,177,74)]">
          <form ref={ref} className="w-[0] hidden transition duration-300">
            <input type="search" onChange={handleInputChange} dir={direction} placeholder="جستوجو" className="w-full focus:outline-none font-[16px] font-[main] placeholder:font-[16px] text-[rgb(220,177,74)] bg-transparent" />
          </form>

          <button className="w-[30px] h-[30px]" onClick={clickHandler}>
            <HiMagnifyingGlass className="w-full h-full duration-300" />
          </button>
        </div>
      </div>
    </>
  );
};

export default SearchBar;
