import React from 'react';
import { Outlet } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import ProjectProgressBar from './ProjectProgressBar';
import {
  AppBar,
  Box,
  Drawer,
  IconButton,
  Toolbar,
  Typography,
  Divider,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Badge,
  Avatar,
  Menu,
  MenuItem,
  Tooltip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  Assignment as AssignmentIcon,
  Message as MessageIcon,
  Settings as SettingsIcon,
  Notifications as NotificationsIcon,
  Brightness4 as Brightness4Icon,
  Brightness7 as Brightness7Icon,
  AccountCircle as AccountCircleIcon,
  ChevronLeft as ChevronLeftIcon,
} from '@mui/icons-material';
import { RootState } from '../store';
import { toggleSidebar, toggleDarkMode, setActiveTab } from '../store/slices/uiSlice';
import { logout } from '../store/slices/authSlice';

const drawerWidth = 240;

const Layout: React.FC = () => {
  const dispatch = useDispatch();
  const { sidebarOpen, darkMode, activeTab, notifications } = useSelector((state: RootState) => state.ui);
  const { user } = useSelector((state: RootState) => state.auth);

  // State for user menu
  const [anchorElUser, setAnchorElUser] = React.useState<null | HTMLElement>(null);
  
  // State for notifications menu
  const [anchorElNotifications, setAnchorElNotifications] = React.useState<null | HTMLElement>(null);

  // Handle opening user menu
  const handleOpenUserMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorElUser(event.currentTarget);
  };

  // Handle closing user menu
  const handleCloseUserMenu = () => {
    setAnchorElUser(null);
  };

  // Handle opening notifications menu
  const handleOpenNotificationsMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorElNotifications(event.currentTarget);
  };

  // Handle closing notifications menu
  const handleCloseNotificationsMenu = () => {
    setAnchorElNotifications(null);
  };

  // Handle logout
  const handleLogout = () => {
    dispatch(logout());
    handleCloseUserMenu();
  };

  // Handle navigation
  const handleNavigation = (tab: RootState['ui']['activeTab']) => {
    dispatch(setActiveTab(tab));
  };

  // Count unread notifications
  const unreadNotificationsCount = notifications.filter(n => !n.read).length;

  // Navigation items
  const navItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, tab: 'dashboard' as const },
    { text: 'Agents', icon: <PeopleIcon />, tab: 'agents' as const },
    { text: 'Tasks', icon: <AssignmentIcon />, tab: 'tasks' as const },
    { text: 'Communication', icon: <MessageIcon />, tab: 'communication' as const },
    { text: 'Settings', icon: <SettingsIcon />, tab: 'settings' as const },
  ];

  return (
    <>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={() => dispatch(toggleSidebar())}
            sx={{ mr: 2 }}
          >
            {sidebarOpen ? <ChevronLeftIcon /> : <MenuIcon />}
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            AI-Orchestration-Platform
          </Typography>

          {/* Toggle dark mode */}
          <Tooltip title={darkMode ? 'Light Mode' : 'Dark Mode'}>
            <IconButton color="inherit" onClick={() => dispatch(toggleDarkMode())}>
              {darkMode ? <Brightness7Icon /> : <Brightness4Icon />}
            </IconButton>
          </Tooltip>

          {/* Notifications */}
          <Tooltip title="Notifications">
            <IconButton color="inherit" onClick={handleOpenNotificationsMenu}>
              <Badge badgeContent={unreadNotificationsCount} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
          </Tooltip>
          <Menu
            sx={{ mt: '45px' }}
            id="notifications-menu"
            anchorEl={anchorElNotifications}
            anchorOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            keepMounted
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            open={Boolean(anchorElNotifications)}
            onClose={handleCloseNotificationsMenu}
          >
            {notifications.length > 0 ? (
              notifications.slice(0, 5).map((notification) => (
                <MenuItem key={notification.id} onClick={handleCloseNotificationsMenu}>
                  <Typography variant="body2" color={notification.type}>
                    {notification.message}
                  </Typography>
                </MenuItem>
              ))
            ) : (
              <MenuItem onClick={handleCloseNotificationsMenu}>
                <Typography variant="body2">No notifications</Typography>
              </MenuItem>
            )}
          </Menu>

          {/* User menu */}
          <Box sx={{ ml: 2 }}>
            <Tooltip title="Open settings">
              <IconButton onClick={handleOpenUserMenu} sx={{ p: 0 }}>
                <Avatar alt={user?.username || 'User'} src="/static/images/avatar/2.jpg" />
              </IconButton>
            </Tooltip>
            <Menu
              sx={{ mt: '45px' }}
              id="menu-appbar"
              anchorEl={anchorElUser}
              anchorOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
              keepMounted
              transformOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
              open={Boolean(anchorElUser)}
              onClose={handleCloseUserMenu}
            >
              <MenuItem onClick={handleCloseUserMenu}>
                <ListItemIcon>
                  <AccountCircleIcon fontSize="small" />
                </ListItemIcon>
                <Typography textAlign="center">Profile</Typography>
              </MenuItem>
              <MenuItem onClick={handleLogout}>
                <Typography textAlign="center">Logout</Typography>
              </MenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="persistent"
        open={sidebarOpen}
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
            top: ['48px', '56px', '64px'],
            height: 'auto',
            bottom: 0,
          },
        }}
      >
        <Divider />
        <List>
          {navItems.map((item) => (
            <ListItem key={item.tab} disablePadding>
              <ListItemButton
                selected={activeTab === item.tab}
                onClick={() => handleNavigation(item.tab)}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Drawer>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${sidebarOpen ? drawerWidth : 0}px)` },
          ml: { sm: sidebarOpen ? `${drawerWidth}px` : 0 },
          mt: ['48px', '56px', '64px'],
          transition: (theme) =>
            theme.transitions.create(['margin', 'width'], {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.leavingScreen,
            }),
        }}
      >
        {/* Project Progress Bar */}
        <Box sx={{ mb: 3 }}>
          <ProjectProgressBar />
        </Box>
        <Outlet />
      </Box>
    </>
  );
};

export default Layout;
