import { AppPlugin } from '@grafana/data';
import { RootPage } from './components/RootPage';

export const plugin = new AppPlugin<{}>().setRootPage(RootPage);
